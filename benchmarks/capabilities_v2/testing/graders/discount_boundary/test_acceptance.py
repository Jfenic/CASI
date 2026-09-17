import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TEST_FILE = "test_discount.py"
MODULES = ["pricing.py"]
MUTANTS = json.loads((Path(__file__).with_name("mutants.json")).read_text())


def run_candidate(root, target, replacement=None):
    target.mkdir()
    for name in MODULES:
        shutil.copy2(root / name, target / name)
    if replacement:
        for name, source in replacement.items():
            (target / name).write_text(source)
    shutil.copy2(root / TEST_FILE, target / TEST_FILE)
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


@pytest.fixture(scope="module")
def correct_result(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    if not (root / TEST_FILE).is_file():
        return None
    return run_candidate(root, tmp_path_factory.mktemp("control") / "correct")


def test_delivery():
    root = Path(__file__).resolve().parents[1]
    assert (root / TEST_FILE).is_file(), "DELIVERY: requested test file missing"


def test_correct_implementation(correct_result):
    assert correct_result is not None, "DELIVERY: requested test file missing"
    assert correct_result.returncode == 0, (
        "CORRECT_IMPLEMENTATION: tests must pass and collect at least one test\n"
        + correct_result.stdout
        + correct_result.stderr
    )


@pytest.mark.parametrize("name", MUTANTS)
def test_detects_mutation(name, correct_result, tmp_path):
    if correct_result is None or correct_result.returncode != 0:
        pytest.skip("Mutation quality unscored: no passing correct-code control")
    root = Path(__file__).resolve().parents[1]
    result = run_candidate(root, tmp_path / name, MUTANTS[name])
    assert result.returncode == 1, (
        f"MUTATION {name}: expected assertion failure (exit 1), "
        f"got {result.returncode}; exit 0 means survived, other codes are errors\n"
        + result.stdout
        + result.stderr
    )
