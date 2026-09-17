"""Validate authored v2 fixtures and references; this does not run a model."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from casi.evaluation.benchmark import load_tasks
from casi.evaluation.grading import grade_task
from casi.sandbox.local_runner import LocalRunner

ROOT = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", choices=("docker", "local"), default="docker")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    runner = LocalRunner() if args.runner == "local" else None
    results = []
    for area in ("testing", "security", "ml"):
        for task in load_tasks(ROOT / area / "tasks"):
            original = ROOT / area / "repositories" / task.repository
            for kind, candidate in (
                ("baseline", original),
                ("reference", ROOT / area / "solutions" / task.repository),
            ):
                result, runner_name = grade_task(
                    task, original=original, candidate=candidate, runner=runner
                )
                expected = 1 if kind == "baseline" else 0
                passed = result.exit_code == expected and not result.timed_out
                results.append(
                    {
                        "area": area,
                        "task_id": task.task_id,
                        "candidate": kind,
                        "runner": runner_name,
                        "expected_exit_code": expected,
                        "exit_code": result.exit_code,
                        "timed_out": result.timed_out,
                        "passed": passed,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }
                )
                print(
                    f"{task.task_id} {kind}: {'PASS' if passed else 'FAIL'}", flush=True
                )
    hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for area in ("testing", "security", "ml")
        for path in sorted((ROOT / area).rglob("*"))
        if path.is_file() and path.suffix in {".py", ".yaml", ".json"}
    }
    payload = {
        "suite": "capabilities_v2",
        "kind": "fixture_validation_not_model_measurement",
        "generated_at": datetime.now(UTC).isoformat(),
        "sha256": hashes,
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
