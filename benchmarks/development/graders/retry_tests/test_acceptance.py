import os
import shutil
import subprocess
import sys
from pathlib import Path

MODULE = "retrying.py"
TEST_FILE = "test_retry.py"
MUTANTS = {
    "no_retry": (
        "def retry(operation, attempts=3):\n"
        "    if attempts < 1:\n"
        '        raise ValueError("attempts must be positive")\n'
        "    return operation()\n"
    ),
    "swallow_error": (
        "def retry(operation, attempts=3):\n"
        "    if attempts < 1:\n"
        '        raise ValueError("attempts must be positive")\n'
        "    for index in range(attempts):\n"
        "        try:\n"
        "            return operation()\n"
        "        except RuntimeError:\n"
        "            if index == attempts - 1:\n"
        "                return None\n"
    ),
    "extra_attempt": (
        "def retry(operation, attempts=3):\n"
        "    if attempts < 1:\n"
        '        raise ValueError("attempts must be positive")\n'
        "    for index in range(attempts + 1):\n"
        "        try:\n"
        "            return operation()\n"
        "        except RuntimeError:\n"
        "            if index == attempts:\n"
        "                raise\n"
    ),
    "catch_all": (
        "def retry(operation, attempts=3):\n"
        "    if attempts < 1:\n"
        '        raise ValueError("attempts must be positive")\n'
        "    for index in range(attempts):\n"
        "        try:\n"
        "            return operation()\n"
        "        except Exception:\n"
        "            if index == attempts - 1:\n"
        "                raise\n"
    ),
    "no_validation": (
        "def retry(operation, attempts=3):\n"
        "    for index in range(attempts):\n"
        "        try:\n"
        "            return operation()\n"
        "        except RuntimeError:\n"
        "            if index == attempts - 1:\n"
        "                raise\n"
    ),
}


def run_generated_tests(root, target):
    env = os.environ.copy()
    env["PYTEST_ADDOPTS"] = ""
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", TEST_FILE],
        cwd=target,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_generated_suite_detects_mutations(tmp_path):
    root = Path(__file__).resolve().parents[1]
    assert (root / TEST_FILE).is_file(), "The requested test file was not created"
    for name, code in [("correct", (root / MODULE).read_text()), *MUTANTS.items()]:
        target = tmp_path / name
        target.mkdir()
        (target / MODULE).write_text(code)
        shutil.copy2(root / TEST_FILE, target / TEST_FILE)
        result = run_generated_tests(root, target)
        expected = 0 if name == "correct" else 1
        assert result.returncode == expected, (
            f"{name}: expected pytest exit {expected}, got {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}"
        )
