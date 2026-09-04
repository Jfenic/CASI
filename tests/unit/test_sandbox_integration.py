from __future__ import annotations

from pathlib import Path

from casi.agent.loop import AgentLoop
from casi.llm.base import LLMResponse
from casi.patching.extract import extract_patch
from casi.sandbox.patched_tests import run_patched_tests
from casi.sandbox.runner_factory import resolve_test_runner
from casi.tools.registry import ToolRegistry


def test_resolve_test_runner_falls_back_to_local_when_docker_disabled() -> None:
    runner, runner_kind = resolve_test_runner(prefer_docker=False)
    assert runner_kind == "local"
    assert runner.__class__.__name__ == "LocalRunner"


def test_resolve_test_runner_prefers_prepared_project_image(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.project_image_if_available",
        lambda _: "casi-project-env:abc",
    )
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.DockerRunner.is_available",
        lambda self: True,
    )
    monkeypatch.setattr(
        "casi.sandbox.runner_factory.DockerRunner.image_exists",
        lambda self: True,
    )

    runner, runner_kind = resolve_test_runner(repository=tmp_path)

    assert runner_kind == "docker"
    assert runner.image == "casi-project-env:abc"


def test_run_patched_tests_applies_patch_on_temporary_copy(tmp_path: Path) -> None:
    target = tmp_path / "sample.py"
    target.write_text("value = 1\n", encoding="utf-8")
    patch = (
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 2\n"
    )
    (tmp_path / "test_sample.py").write_text(
        "from sample import value\n\n"
        "def test_value():\n"
        "    assert value == 2\n",
        encoding="utf-8",
    )

    result, runner_kind = run_patched_tests(
        tmp_path,
        patch,
        prefer_docker=False,
    )

    assert runner_kind == "local"
    assert result.exit_code == 0
    assert target.read_text(encoding="utf-8") == "value = 1\n"


def test_extract_patch_reads_fenced_diff() -> None:
    response = "Here is the fix:\n```diff\n--- a/x.py\n+++ b/x.py\n```\n"
    assert extract_patch(response) == "--- a/x.py\n+++ b/x.py\n"


class CorrectionClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = iter(responses)
        self.calls = 0

    def complete(self, messages, tools):
        self.calls += 1
        return next(self.responses)


def test_agent_loop_retries_patch_when_sandbox_tests_fail(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "from sample import value\n\n"
        "def test_value():\n"
        "    assert value == 2\n",
        encoding="utf-8",
    )
    bad_patch = (
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 1\n"
    )
    good_patch = (
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 2\n"
    )
    client = CorrectionClient(
        [
            LLMResponse.final(f"Broken patch\n{bad_patch}"),
            LLMResponse.final(f"Fixed patch\n{good_patch}"),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=2,
    ).run("Fix the failing test")

    assert result.success is True
    assert client.calls == 2
    assert result.patch_verification is not None
    assert result.patch_verification.passed is True
    assert result.patch_verification.runner in {"local", "docker"}
    assert result.patch_verification.correction_attempts == 1


def test_agent_loop_retries_patch_when_patch_is_invalid(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "from sample import value\n\n"
        "def test_value():\n"
        "    assert value == 2\n",
        encoding="utf-8",
    )
    invalid_patch = (
        "--- a/missing.py\n"
        "+++ b/missing.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 2\n"
    )
    good_patch = (
        "--- a/sample.py\n"
        "+++ b/sample.py\n"
        "@@ -1 +1 @@\n"
        "-value = 1\n"
        "+value = 2\n"
    )
    client = CorrectionClient(
        [
            LLMResponse.final(f"Invalid patch\n{invalid_patch}"),
            LLMResponse.final(f"Fixed patch\n{good_patch}"),
        ]
    )

    result = AgentLoop(
        client,
        ToolRegistry(tmp_path),
        max_correction_attempts=2,
    ).run("Fix the failing test")

    assert result.success is True
    assert client.calls == 2
    assert result.patch_verification is not None
    assert result.patch_verification.passed is True
    assert result.patch_verification.correction_attempts == 1
