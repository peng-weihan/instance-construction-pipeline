"""Bounded real Codex rollouts with private-file isolation and frozen final grading.

Raw events remain authoritative. Only observed messages and completed shell actions
are adapted to SFT; lossy file-change events fail the full-trajectory export gate.
macOS pilot runner: absence of a working sandbox is a hard error, never a fallback.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import threading
import time

from .calibrate import write_json
from .contract import digest, official_score, read_instance, verify_solution
from .pack import snapshot

PROJECT = Path(__file__).resolve().parents[1]
JUDGE_TEMP = Path('/private/tmp/edge-training-judge')
WORK_TEMP = Path('/private/tmp/edge-training-work')


def seatbelt(denied, writable=None):
    paths = ' '.join('(subpath ' + json.dumps(str(Path(p).resolve())) + ')' for p in denied)
    if writable is None:
        # Permit metadata/path canonicalization, but never file contents or directory listings.
        return f'(version 1) (allow default) (deny file-read-data {paths}) (deny file-write* {paths})'
    return ('(version 1) (deny default) (allow process*) (allow sysctl-read) '
        '(allow mach-lookup) (allow ipc-posix*) (allow file-read*) '
        f'(deny file-read* {paths}) '
        f'(allow file-write* (subpath {json.dumps(str(Path(writable).resolve()))}) (literal "/dev/null"))')


def codex_binary():
    executable = Path(shutil.which('codex')).resolve()
    # The npm executable is a Node launcher. Use its bundled native binary when present.
    native = list(executable.parent.parent.glob('node_modules/@openai/codex-*/vendor/*/bin/codex'))
    return str(native[0] if len(native) == 1 else executable)


def captured(argv, cwd, timeout, profile=None, env=None):
    if profile:
        argv = ['/usr/bin/sandbox-exec', '-p', profile, *map(str, argv)]
    process = subprocess.Popen(list(map(str, argv)), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True, env=env)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate()
    return {'argv': list(map(str, argv[3:] if profile else argv)), 'returncode': process.returncode,
            'stdout': stdout[-100_000:], 'stderr': stderr[-100_000:], 'timed_out': timed_out}


def decode_submission(files):
    if not isinstance(files, dict) or len(files) > 200:
        raise ValueError('Invalid submission file map')
    decoded = {}
    for name, data in files.items():
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or not (name == 'Makefile' or p.parts[0] in ['src', 'include']):
            raise ValueError('Submission path outside allowlist')
        decoded[name] = base64.b64decode(data, validate=True)
    if sum(map(len, decoded.values())) > 3_000_000 or 'src/solver.cpp' not in decoded or 'Makefile' not in decoded:
        raise ValueError('Incomplete or oversized submission')
    return decoded


def source_files(work):
    files = {}
    for top in ['src', 'include', 'Makefile']:
        target = Path(work) / top
        paths = [target] if target.is_file() else sorted(target.rglob('*'))
        for path in paths:
            if path.is_symlink():
                raise ValueError('No symlinks in submissions')
            if path.is_file():
                files[str(path.relative_to(work))] = base64.b64encode(path.read_bytes()).decode()
    decode_submission(files)
    return files


def grade(task, files, output, split='feedback', budget=1):
    task, output = Path(task), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((task / 'manifest.json').read_text())
    if snapshot(task / 'judge') != manifest['judge_sha256']:
        raise ValueError('Frozen judge assets changed')
    cases = json.loads((task / 'judge/cases.json').read_text())[split]
    if not cases or any(not r['reference']['valid'] for r in cases):
        raise ValueError('Missing/invalid reference: fail closed')
    decoded = decode_submission(files)
    write_json(output / 'submission.json', files)
    JUDGE_TEMP.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='eval-', dir=JUDGE_TEMP) as temporary:
        working = Path(temporary)
        for name, content in decoded.items():
            target = working / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        shutil.copytree(task / 'work/tools', working / 'tools')
        (working / '.tmp').mkdir()
        env = {**os.environ, 'TMPDIR': str(working / '.tmp'), 'CLANG_MODULE_CACHE_PATH': str(working / '.tmp/modules')}
        profile = seatbelt([PROJECT, Path.home() / '.codex', WORK_TEMP], writable=working)
        build = captured(['make', '-B'], working, 60, profile, env)
        write_json(output / 'build.json', build)
        details = []
        for row in cases:
            result = {'valid': False, 'reason': 'compile', 'nv': None, 'td': None}
            if build['returncode'] == 0 and not build['timed_out']:
                # Only one hidden input exists in the solver's execution directory at a time.
                input_path, solution_path = working / 'input.txt', working / 'solution.txt'
                shutil.copy2(task / 'judge' / split / row['filename'], input_path)
                if solution_path.exists():
                    solution_path.unlink()
                execution = captured([working / 'cvrptw_solver', input_path, solution_path, str(budget)],
                                     working, budget + 2, profile, env)
                if execution['returncode'] == 0 and not execution['timed_out']:
                    result = verify_solution(read_instance(input_path), solution_path)
                    native = captured([PROJECT / 'runs/alignment-calibration-001/tools/original_verify',
                                       input_path, solution_path], working, 5)
                    # Original checker plus independent parser must both pass.
                    if native['returncode'] != 0:
                        result = {'valid': False, 'reason': 'native_verifier', 'nv': None, 'td': None}
                    execution['native_verifier'] = native
                else:
                    result['reason'] = 'timeout' if execution['timed_out'] else 'process_exit'
                write_json(output / (row['name'] + '.execution.json'), execution)
                if solution_path.exists():
                    shutil.copy2(solution_path, output / (row['name'] + '.sol'))
                input_path.unlink()
            details.append({'name': row['name'], 'family': row['family'], **result,
                            'score': official_score(result, row['reference'])})
        score = sum(x['score'] for x in details) / len(cases)
        report = {'split': split, 'raw_score': score, 'normalized_score': min(score / 100, 1),
            'valid_cases': sum(x['valid'] for x in details), 'total_cases': len(cases),
            'all_feasible': all(x['valid'] for x in details), 'source_sha256': digest(files),
            'per_case_budget_seconds': budget, 'details': details, 'sandbox': 'macos-seatbelt',
            'full_original_budget': False}
        write_json(output / 'report.json', report)
        return report


def aggregate(report):
    return {k: report[k] for k in ['raw_score', 'valid_cases', 'total_cases', 'all_feasible', 'per_case_budget_seconds']}


def adapt_events(events, prompt):
    """Observed shell commands => a declared shell tool; never invent missing edits."""
    messages, problems = [{'role': 'user', 'content': prompt}], []
    completed = False
    count = 0
    for event in events:
        if event.get('type') == 'turn.completed':
            completed = True
        if event.get('type') in ['turn.failed', 'error']:
            problems.append('event_error')
        if event.get('type') != 'item.completed':
            continue
        item = event['item']
        kind = item.get('type')
        if kind == 'command_execution':
            if item.get('status') not in ['completed', 'failed'] or 'command' not in item:
                problems.append('incomplete_command')
                continue
            call_id = item.get('id', f'command_{count}')
            messages.append({'role': 'assistant', 'tool_calls': [{'id': call_id, 'type': 'function',
                'function': {'name': 'shell', 'arguments': json.dumps({'command': item['command']})}}]})
            messages.append({'role': 'tool', 'tool_call_id': call_id, 'content': json.dumps({
                'output': item.get('aggregated_output', ''), 'exit_code': item.get('exit_code')})})
            count += 1
        elif kind == 'agent_message':
            messages.append({'role': 'assistant', 'content': item['text']})
        elif kind == 'reasoning':
            continue  # Do not export private reasoning or fabricate explanatory chains.
        elif kind == 'mcp_tool_call' and item.get('server') == 'edge_shell' and item.get('tool') == 'shell':
            arguments = item.get('arguments')
            result = item.get('result')
            if arguments is None or result is None:
                problems.append('missing_mcp_payload')
                continue
            call_id = item.get('id', f'command_{count}')
            messages.append({'role': 'assistant', 'tool_calls': [{'id':call_id, 'type':'function',
                'function': {'name':'shell', 'arguments': json.dumps(arguments)}}]})
            messages.append({'role':'tool','tool_call_id':call_id,'content':json.dumps(result)})
            count += 1
        elif kind in ['file_change', 'mcp_tool_call', 'web_search']:
            problems.append('non_replayable_' + kind)
    if not completed:
        problems.append('turn_not_completed')
    if not count:
        problems.append('no_executed_commands')
    return {'messages': messages, 'problems': sorted(set(problems)), 'command_count': count,
            'tools': [{'type': 'function', 'function': {'name': 'shell', 'description': 'Execute a shell command in the task workspace.',
                'parameters': {'type': 'object', 'properties': {'command': {'type': 'string'},
                    'timeout_seconds': {'type':'integer'}}, 'required': ['command']}}}]}


def run_teacher(task, output, model='gpt-6.1-sol', seconds=600):
    task, output = Path(task).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    policy = json.loads((task / 'policy.json').read_text())
    WORK_TEMP.mkdir(exist_ok=True)
    JUDGE_TEMP.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=task.name + '-', dir=WORK_TEMP))
    shutil.copytree(task / 'work', work, dirs_exist_ok=True)
    (work / '.feedback').mkdir()
    (work / '.teacher_tools').mkdir()
    shutil.copy2(Path(__file__).with_name('mcp_bridge.py'), work / 'mcp_bridge.py')
    # No task-private metadata is copied to the teacher. The other teacher also gets a distinct directory.
    # A separate CLI home prevents it from opening historical sessions containing author data.
    # The locally logged-in credential is copied only into this private temporary directory;
    # its bytes never enter logs, prompts, or exported datasets.
    cli_home = Path(tempfile.mkdtemp(prefix='edge-cli-home-', dir='/private/tmp'))
    cli_home.chmod(0o700)
    original_auth = Path.home() / '.codex/auth.json'
    if original_auth.exists():
        shutil.copyfile(original_auth, cli_home / 'auth.json')
        (cli_home / 'auth.json').chmod(0o600)
    denied = [PROJECT, JUDGE_TEMP, Path.home() / '.codex',
              *[p for p in WORK_TEMP.iterdir() if p != work]]
    profile = seatbelt(denied)
    # Deny sibling workspaces, including ones created after this process starts.
    siblings = (f'(require-all (subpath {json.dumps(str(WORK_TEMP))}) '
                f'(require-not (subpath {json.dumps(str(work))})))')
    profile += f' (deny file-read-data {siblings}) (deny file-write* {siblings})'
    probe_hidden = captured(['/bin/cat', task / 'policy.json'], work, 10, profile)
    probe_public = captured(['/bin/cat', work / 'include/types.h'], work, 10, profile)
    isolation = {'private_read_denied': probe_hidden['returncode'] != 0 and 'Operation not permitted' in probe_hidden['stderr'],
                 'public_read_allowed': probe_public['returncode'] == 0, 'denied_roots': list(map(str, denied))}
    write_json(output / 'isolation.json', isolation)
    if not all(isolation[k] for k in ['private_read_denied', 'public_read_allowed']):
        raise RuntimeError('Isolation preflight failed; teacher was not started')
    initial = source_files(work)
    write_json(output / 'initial_submission.json', initial)
    # Baseline measured with exactly the same feedback budget as all subsequent teacher submissions.
    baseline = grade(task, initial, output / 'baseline', budget=policy['feedback_budget_seconds'])
    prompt = ('Read README.md and optimize the supplied C++17 solver. You have at most '
              f'{seconds} seconds. Use feedback.py for aggregate feedback; preserve a feasible best solution. '
              'Only modify src/, include/, Makefile. Use shell commands for all edits to retain an exact '
              'execution trace. Do not use subagents, network access, hidden files, external solvers or apply_patch. '
              'IMPORTANT: Use ONLY the MCP edge_shell.shell tool for all filesystem reads, shell commands, '
              'edits, builds, tests and feedback. Native shell tools cannot run in this nested macOS environment. '
              'The MCP tool runs the same commands through an isolated execution service. '
              'Finish with a brief summary of implemented changes and actual tests.')
    (output / 'prompt.txt').write_text(prompt)
    native = codex_binary()
    teacher_env = {**os.environ, 'CODEX_HOME': str(cli_home), 'PWD': str(work)}
    cli_probe = captured([native, '--version'], work, 10, profile, teacher_env)
    write_json(output / 'cli_preflight.json', cli_probe)
    if cli_probe['returncode'] != 0:
        raise RuntimeError('Native Codex preflight failed; no model inference started')
    argv = [native, '--no-daemon', 'exec', '--json', '--ephemeral', '--ignore-user-config', '--ignore-rules',
            '--disable', 'apps', '--disable', 'plugins', '--disable', 'shell_tool', '--disable', 'unified_exec',
            '--disable', 'shell_snapshot', '--disable', 'computer_use', '--disable', 'browser_use',
            '--enable', 'skip_host_skill_discovery',
            '--skip-git-repo-check', '--sandbox', 'workspace-write', '--model', model,
            '-c', 'model_reasoning_effort="low"', '-c', 'approval_policy="never"',
            '-c', 'mcp_servers.edge_shell.command="/opt/homebrew/bin/python3.12"',
            '-c', 'mcp_servers.edge_shell.args=' + json.dumps([str(work / 'mcp_bridge.py')]),
            '-c', 'mcp_servers.edge_shell.tool_timeout_sec=200',
            '-c', 'mcp_servers.edge_shell.tools.shell.approval_mode="approve"',
            '-c', 'mcp_servers.edge_shell.required=true',
            '-C', str(work), '-']
    write_json(output / 'launch.json', {'argv': argv, 'model': model, 'reasoning_effort': 'low',
        'max_seconds': seconds, 'policy': policy, 'workdir': str(work), 'source': 'real_codex_cli',
        'cli_version': cli_probe['stdout'].strip()})
    started = time.monotonic()
    timed_out = False
    feedback, processed = [], set()
    with (output / 'events.jsonl').open('w') as stdout, (output / 'stderr.log').open('w') as stderr:
        process = subprocess.Popen(['/usr/bin/sandbox-exec', '-p', profile, *argv], cwd=work,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True,
            env=teacher_env)
        write_json(output / 'process.json', {'pid':process.pid})
        def copy_stream(source, destination):
            for line in source:
                destination.write(line)
                destination.flush()
        stdout_thread = threading.Thread(target=copy_stream, args=(process.stdout, stdout))
        stderr_thread = threading.Thread(target=copy_stream, args=(process.stderr, stderr))
        stdout_thread.start()
        stderr_thread.start()
        process.stdin.write(prompt)
        process.stdin.close()
        with ThreadPoolExecutor(max_workers=2) as executor:
            active = None
            active_path = None
            tool_active = None
            tool_path = None
            tool_processed = set()
            tool_profile = seatbelt([PROJECT, JUDGE_TEMP, Path.home() / '.codex', cli_home], writable=work)
            tool_profile += f' (deny file-read-data {siblings})'
            (work / '.tmp').mkdir(exist_ok=True)
            tool_env = {**os.environ, 'PWD':str(work), 'TMPDIR':str(work / '.tmp'),
                        'CLANG_MODULE_CACHE_PATH':str(work / '.tmp/modules')}
            while process.poll() is None:
                if time.monotonic() - started >= seconds:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                    break
                if tool_active is not None and tool_active.done():
                    try:
                        result = tool_active.result()
                    except Exception as exc:
                        result = {'error':str(exc)}
                    result['request_id'] = tool_path.name.split('.')[0]
                    write_json(output / 'tool_commands' / tool_path.name.replace('.request.','.response.'), result)
                    write_json(tool_path.with_name(tool_path.name.replace('.request.','.response.')), result)
                    tool_active = None
                if tool_active is None:
                    for path in sorted((work / '.teacher_tools').glob('*.request.json')):
                        if path.name in tool_processed:
                            continue
                        tool_processed.add(path.name)
                        tool_path = path
                        request = json.loads(path.read_text())
                        arguments = request['arguments']
                        command = arguments.get('command')
                        if not isinstance(command, str) or len(command) > 1_000_000:
                            write_json(path.with_name(path.name.replace('.request.','.response.')), {'error':'invalid command'})
                            continue
                        write_json(output / 'tool_commands' / path.name, request)
                        timeout = min(max(int(arguments.get('timeout_seconds',120)),1),180,
                                      max(1, int(seconds - (time.monotonic() - started))))
                        tool_active = executor.submit(captured, ['/bin/bash', '--noprofile', '--norc', '-c', command], work, timeout, tool_profile, tool_env)
                        break
                if active is not None and active.done():
                    try:
                        report = active.result()
                        feedback.append(report)
                        response = aggregate(report)
                    except Exception as exc:
                        response = {'error': str(exc)}
                    write_json(active_path.with_name(active_path.name.replace('.request.', '.response.')), response)
                    active = None
                if active is None:
                    for path in sorted((work / '.feedback').glob('*.request.json')):
                        if path.name in processed:
                            continue
                        processed.add(path.name)
                        active_path = path
                        try:
                            request = json.loads(path.read_text())
                            decode_submission(request['files'])
                            active = executor.submit(grade, task, request['files'], output / 'feedback' / path.stem,
                                budget=policy['feedback_budget_seconds'])
                        except Exception as exc:
                            write_json(path.with_name(path.name.replace('.request.', '.response.')), {'error': str(exc)})
                        break
                time.sleep(.2)
            if active is not None:
                try:
                    feedback.append(active.result())
                except Exception:
                    pass
        process.wait()
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
    inference_elapsed = time.monotonic() - started
    # Remove only the ephemeral credential copy created by this invocation.
    if (cli_home / 'auth.json').exists():
        (cli_home / 'auth.json').unlink()
    final_files = source_files(work)
    write_json(output / 'final_submission.json', final_files)
    # Atomic lock: final grading cannot become an iterative feedback channel.
    with (output / 'final.lock').open('x') as lock:
        lock.write(digest(final_files))
    final = grade(task, final_files, output / 'final', split='final', budget=policy['final_budget_seconds'])
    events = []
    parse_error = False
    for line in (output / 'events.jsonl').read_text().splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            parse_error = True
    adapted = adapt_events(events, prompt)
    final_feedback = [r for r in feedback if r['source_sha256'] == digest(final_files)]
    gain = max((r['raw_score'] for r in final_feedback), default=0) - baseline['raw_score']
    checks = {'real_completed_trace': process.returncode == 0 and not timed_out and not parse_error and not adapted['problems'],
        'private_files_denied': isolation['private_read_denied'], 'all_final_feasible': final['all_feasible'],
        'final_score': final['raw_score'] >= policy['minimum_final_raw_score'],
        'feedback_improved': bool(final_feedback) and gain >= policy['minimum_feedback_gain'],
        'code_changed': digest(final_files) != digest(initial)}
    quality = {'accepted': all(checks.values()), 'checks': checks, 'model': model, 'reasoning_effort': 'low',
        'returncode': process.returncode, 'timed_out': timed_out, 'wall_seconds': time.monotonic() - started,
        'teacher_seconds': inference_elapsed, 'baseline': aggregate(baseline),
        'final': aggregate(final), 'feedback_gain': gain, 'trace_problems': adapted['problems'],
        'command_count': adapted['command_count'], 'source_sha256': digest(final_files),
        'events_sha256': hashlib.sha256((output / 'events.jsonl').read_bytes()).hexdigest()}
    write_json(output / 'quality.json', quality)
    if quality['accepted']:
        record = {'task_id': task.name, 'teacher_model': model, 'messages': adapted['messages'], 'tools': adapted['tools'],
            'final_code': {k: base64.b64decode(v).decode() for k, v in final_files.items()}, 'quality': quality,
            'initial_files': {str(p.relative_to(task / 'work')): p.read_text()
                              for p in (task / 'work').rglob('*') if p.is_file()},
            'provenance': {'kind': 'real_codex_cli_shell_event_adapter', 'private_reasoning_exported': False,
                           'tool_argument_adapter': 'observed CLI command string -> shell.command'}}
        write_json(output / 'sft.jsonl', record)
    print(json.dumps({'task': task.name, **quality}), flush=True)
    return quality


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--task', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model', default='gpt-6.1-sol')
    parser.add_argument('--seconds', type=int, default=600)
    args = parser.parse_args()
    run_teacher(args.task, args.output, args.model, args.seconds)
