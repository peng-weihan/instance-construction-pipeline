"""Validate immutable candidate artifacts and structured authoritative scores."""
import io
import json
import math
from pathlib import Path, PurePosixPath
import tarfile

def validate_artifacts(paths):
    if not paths:
        raise ValueError('Explicit artifact paths are required')
    protected = ['/tests', '/logs', '/etc', '/proc', '/sys', '/dev', '/bin', '/sbin',
                 '/usr', '/lib', '/lib64', '/edgebench-ipc', '/tmp/codex-home',
                 '/tmp/codex-secrets', '/tmp/edgebench-adapter', '/root/.codex', '/opt/edgebench-codex', '/opt/codex-static']
    for raw in paths:
        p = PurePosixPath(raw)
        if not p.is_absolute() or '..' in p.parts or str(p) == '/':
            raise ValueError('Artifact path must be absolute and normalized: ' + raw)
        for name in protected:
            q = PurePosixPath(name)
            if p == q or p in q.parents or q in p.parents:
                raise ValueError('Artifact path overlaps protected runtime/grader path: ' + raw)

def extract_safe(data, root, allowed_paths, limit=64 * 1024 * 1024):
    validate_artifacts(allowed_paths)
    root = Path(root)
    allowed = [PurePosixPath(p.rstrip('/')) for p in allowed_paths]
    total = 0
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for item in archive:
            rel = PurePosixPath(item.name)
            absolute = PurePosixPath('/') / rel
            if rel.is_absolute() or '..' in rel.parts or not item.isfile():
                raise ValueError('Unsafe archive member: ' + item.name)
            if not any(absolute == p or p in absolute.parents for p in allowed):
                raise ValueError('Archive member outside declared artifacts: ' + item.name)
            if item.name in seen:
                raise ValueError('Duplicate archive member')
            seen.add(item.name)
            total += item.size
            if total > limit:
                raise ValueError('Archive exceeds uncompressed byte limit')
            target = root.joinpath(*rel.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(item) as source, target.open('wb') as dest:
                while chunk := source.read(1024 * 1024):
                    dest.write(chunk)
            target.chmod(item.mode & 0o777)

def parse_report(log_dir, stdout, returncode):
    """Require a structured report; never manufacture a reward on infrastructure error."""
    candidates = [Path(log_dir) / 'score.json', Path(log_dir) / 'result.json']
    report = None
    for path in candidates:
        if path.is_file():
            report = json.loads(path.read_text())
            break
    if report is None:
        start = stdout.rfind('>>>>> Start Structured Result')
        end = stdout.find('>>>>> End Structured Result', start)
        if start >= 0 and end > start:
            report = json.loads(stdout[start + len('>>>>> Start Structured Result'):end].strip())
    if not isinstance(report, dict):
        raise ValueError('Verifier produced no structured score.json/result.json or marked JSON stdout')
    if returncode != 0:
        raise ValueError('Verifier exited nonzero: ' + str(returncode))
    if report.get('infrastructure_error'):
        raise ValueError('Verifier reports infrastructure/parser errors')
    # An evaluator's error count can describe a legitimate invalid submission.
    # Require diagnostics instead of mistaking every candidate error for host failure.
    if report.get('errors') and not report.get('details') and not report.get('checks'):
        raise ValueError('Verifier reports errors without submission diagnostics')
    if not isinstance(report.get('valid'), bool):
        raise ValueError('Structured report must explicitly contain boolean valid')
    score = report.get('score')
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
        raise ValueError('Structured report must contain a finite numeric score')
    # Never infer pass rate from score: optimization scores often have unrelated units.
    if 'pass_rate' not in report:
        if 'certified' in report or 'targets_total' in report:
            certified = report.get('certified')
            total = report.get('targets_total')
            if type(certified) is not int or type(total) is not int or total <= 0 or not 0 <= certified <= total:
                raise ValueError('Invalid certified/targets_total counts')
            report['pass_rate'] = certified / total
        else:
            checks = report.get('checks', [])
            if not isinstance(checks, list) or not checks or any(not isinstance(c, dict) for c in checks):
                raise ValueError('Verifier must provide pass_rate, certified/targets_total or an explicit checks list')
            report['pass_rate'] = sum(bool(c.get('passed')) for c in checks) / len(checks)
    pr = report['pass_rate']
    if isinstance(pr, bool) or not isinstance(pr, (int, float)) or not math.isfinite(pr) or not 0 <= pr <= 1:
        raise ValueError('Invalid pass_rate')
    return report
