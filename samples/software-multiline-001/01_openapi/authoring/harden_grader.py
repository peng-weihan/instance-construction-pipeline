from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'tests/grader.py'
s=p.read_text()
a=s.index('    p = subprocess.Popen(')
b=s.index('\n\ndef grade(', a)
s=s[:a]+'''    import resource
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
        if sys.platform.startswith("linux"):
            resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        p = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                             start_new_session=True, text=True, preexec_fn=limits, **user)
        timed_out = False
        try:
            p.communicate(stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(p.pid, signal.SIGKILL)
            p.communicate()
        finally:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        stdout.seek(0)
        stderr.seek(0)
        return {"command": command, "cwd": str(cwd), "exit": p.returncode,
                "stdout": stdout.read(16000).decode(errors="replace"),
                "stderr": stderr.read(16000).decode(errors="replace"), "timeout": timed_out}
''' + s[b:]
p.write_text(s)
