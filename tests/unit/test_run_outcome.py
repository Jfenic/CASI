from __future__ import annotations

from pathlib import Path

from casi.agent.orchestrator import OrchestratorResult
from casi.agent.run_outcome import resolve_agent_run_outcome
from casi.agent.state import PatchVerification


def test_resolve_agent_run_outcome_keeps_failed_patch_metadata(tmp_path: Path) -> None:
    patch = "--- a/sample.py\n+++ b/sample.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"
    (tmp_path / "sample.py").write_text("value = 1\n", encoding="utf-8")
    result = OrchestratorResult(
        success=False,
        response=f"Broken fix\n{patch}",
        error="Patch verification failed after exhausting correction attempts",
        patch_verification=PatchVerification(
            passed=False,
            output="assert value == 2",
            runner="local",
            correction_attempts=2,
        ),
        requested_code_change=True,
    )

    outcome = resolve_agent_run_outcome(tmp_path, result)

    assert outcome.patch == patch
    assert outcome.patch_valid is False
    assert outcome.tests_passed is False
    assert outcome.test_runner == "local"
