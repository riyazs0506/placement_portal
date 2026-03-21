"""
services/compiler.py — Secure code execution sandbox.
"""
import subprocess, tempfile, os, time


TIMEOUT = 10  # seconds
MAX_OUTPUT = 5000


def run_code(code: str, language: str, stdin_input: str = "") -> dict:
    lang = language.lower()
    try:
        if lang == "python":
            return _run_python(code, stdin_input)
        elif lang in ("c", "cpp"):
            return _run_c_cpp(code, lang, stdin_input)
        elif lang == "java":
            return _run_java(code, stdin_input)
        else:
            return {"stdout": "", "stderr": f"Unsupported language: {lang}", "error": True}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "error": True}


def _run_python(code, stdin_input):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        fname = f.name
    try:
        result = subprocess.run(
            ["python3", fname],
            input=stdin_input, capture_output=True, text=True, timeout=TIMEOUT
        )
        return {
            "stdout": result.stdout[:MAX_OUTPUT],
            "stderr": result.stderr[:MAX_OUTPUT],
            "error": result.returncode != 0,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Time limit exceeded (10s)", "error": True}
    finally:
        os.unlink(fname)


def _run_c_cpp(code, lang, stdin_input):
    ext = ".c" if lang == "c" else ".cpp"
    compiler = "gcc" if lang == "c" else "g++"
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, f"main{ext}")
        exe = os.path.join(tmpdir, "a.out")
        with open(src, "w") as f:
            f.write(code)
        compile_result = subprocess.run(
            [compiler, src, "-o", exe, "-lm"],
            capture_output=True, text=True, timeout=30
        )
        if compile_result.returncode != 0:
            return {"stdout": "", "stderr": compile_result.stderr[:MAX_OUTPUT], "error": True}
        try:
            run_result = subprocess.run(
                [exe], input=stdin_input, capture_output=True, text=True, timeout=TIMEOUT
            )
            return {
                "stdout": run_result.stdout[:MAX_OUTPUT],
                "stderr": run_result.stderr[:MAX_OUTPUT],
                "error": run_result.returncode != 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Time limit exceeded (10s)", "error": True}


def _run_java(code, stdin_input):
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "Main.java")
        with open(src, "w") as f:
            f.write(code)
        compile_result = subprocess.run(
            ["javac", src], capture_output=True, text=True, timeout=30
        )
        if compile_result.returncode != 0:
            return {"stdout": "", "stderr": compile_result.stderr[:MAX_OUTPUT], "error": True}
        try:
            run_result = subprocess.run(
                ["java", "-cp", tmpdir, "Main"],
                input=stdin_input, capture_output=True, text=True, timeout=TIMEOUT
            )
            return {
                "stdout": run_result.stdout[:MAX_OUTPUT],
                "stderr": run_result.stderr[:MAX_OUTPUT],
                "error": run_result.returncode != 0,
            }
        except subprocess.TimeoutExpired:
            return {"stdout": "", "stderr": "Time limit exceeded (10s)", "error": True}
