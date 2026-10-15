import subprocess
from pathlib import Path
EXE = str(Path("executable").resolve())

def test_bytes_0():
    p = subprocess.run([EXE], input=b'hello', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'hello'
    assert p.stderr == b""

def test_bytes_1():
    p = subprocess.run([EXE], input=b'a\n', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'a\n'
    assert p.stderr == b""

def test_bytes_2():
    p = subprocess.run([EXE], input=b'\x00\xff', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'\x00\xff'
    assert p.stderr == b""

def test_bytes_3():
    p = subprocess.run([EXE], input=b'\xe4\xb8\xad\xe6\x96\x87', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'\xe4\xb8\xad\xe6\x96\x87'
    assert p.stderr == b""

def test_bytes_4():
    p = subprocess.run([EXE], input=b' ', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b' '
    assert p.stderr == b""

def test_bytes_5():
    p = subprocess.run([EXE], input=b'123', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'123'
    assert p.stderr == b""

def test_bytes_6():
    p = subprocess.run([EXE], input=b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    assert p.stderr == b""

def test_bytes_7():
    p = subprocess.run([EXE], input=b'a\r\nb', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'a\r\nb'
    assert p.stderr == b""

def test_bytes_8():
    p = subprocess.run([EXE], input=b'Z', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'Z'
    assert p.stderr == b""

def test_bytes_9():
    p = subprocess.run([EXE], input=b'!@#', capture_output=True, timeout=5)
    assert p.returncode == 0
    assert p.stdout == b'!@#'
    assert p.stderr == b""

def test_weak_exit():
    assert subprocess.run([EXE], input=b"", capture_output=True).returncode == 0

def test_error():
    p = subprocess.run([EXE,"--invalid"], capture_output=True, timeout=5)
    assert p.returncode == 2
    assert p.stderr == b"unknown option\n"
