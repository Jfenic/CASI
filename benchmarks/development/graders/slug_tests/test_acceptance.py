import os
import shutil
import subprocess
import sys
from pathlib import Path

MODULE = "slug.py"
TEST_FILE = "test_slug.py"
MUTANTS = {
    "uppercase": (
        "import re\n"
        "\n"
        "def slugify(text):\n"
        '    return re.sub(r"[^a-z0-9]+", "-", text.strip()).strip("-")\n'
    ),
    "spaces_only": (
        "import re\n"
        "\n"
        "def slugify(text):\n"
        '    return re.sub(r" +", "-", text.strip().lower()).strip("-")\n'
    ),
    "edge_hyphens": (
        "import re\n"
        "\n"
        "def slugify(text):\n"
        '    return re.sub(r"[^a-z0-9]+", "-", text.strip().lower())\n'
    ),
    "no_collapse": (
        "import re\n"
        "\n"
        "def slugify(text):\n"
        '    return re.sub(r"[^a-z0-9]", "-", text.strip().lower()).strip("-")\n'
    ),
    "drops_digits": (
        "import re\n"
        "\n"
        "def slugify(text):\n"
        '    return re.sub(r"[^a-z]+", "-", text.strip().lower()).strip("-")\n'
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
