from __future__ import annotations

import subprocess
from pathlib import Path

from casi.patching.validator import validate_patch
from casi.patching.applier import PatchApplicationError, apply_patch
from casi.tools.registry import ToolRegistry


def _git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repo"
    repository.mkdir()
    _git(repository, "init", "--initial-branch", "main")
    _git(repository, "config", "user.email", "tests@example.com")
    _git(repository, "config", "user.name", "CASI Tests")
    (repository / "app.py").write_text("return False\n", encoding="utf-8")
    _git(repository, "add", "app.py")
    _git(repository, "commit", "-m", "initial")
    return repository


VALID_PATCH = """--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-return False
+return True
"""


def test_validate_patch_accepts_applicable_patch(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    result = validate_patch(repository, VALID_PATCH)

    assert result.valid is True
    assert result.files == ["app.py"]
    assert (repository / "app.py").read_text(encoding="utf-8") == "return False\n"


def test_validate_patch_recounts_incorrect_model_hunk_lengths(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    patch = VALID_PATCH.replace("@@ -1 +1 @@", "@@ -1,11 +1,11 @@")

    result = validate_patch(repository, patch)

    assert result.valid is True


def test_apply_patch_recounts_incorrect_model_hunk_lengths(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    patch = VALID_PATCH.replace("@@ -1 +1 @@", "@@ -1,11 +1,11 @@")

    apply_patch(repository, patch, approved=True, dry_run=False)

    assert (repository / "app.py").read_text(encoding="utf-8") == "return True\n"


def test_validate_patch_tool_returns_structured_result(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    result = ToolRegistry(repository).execute("validate_patch", {"patch": VALID_PATCH})

    assert result.success is True
    assert result.output == "Patch is valid"
    assert result.metadata["files"] == ["app.py"]


def test_validate_patch_rejects_invalid_format(tmp_path: Path) -> None:
    result = validate_patch(tmp_path, "not a diff")

    assert result.valid is False
    assert "headers" in (result.error or "")


def test_validate_patch_rejects_unsafe_and_sensitive_paths(tmp_path: Path) -> None:
    traversal = validate_patch(tmp_path, "--- a/../secret.py\n+++ b/../secret.py\n")
    sensitive = validate_patch(tmp_path, "--- a/.env\n+++ b/.env\n")

    assert traversal.valid is False
    assert "Unsafe" in (traversal.error or "")
    assert sensitive.valid is False
    assert "Sensitive" in (sensitive.error or "")


def test_validate_patch_rejects_patch_that_does_not_apply(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    patch = VALID_PATCH.replace("return False", "missing line")

    result = validate_patch(repository, patch)

    assert result.valid is False
    assert result.error


def test_apply_patch_dry_run_does_not_modify_repository(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    files = apply_patch(repository, VALID_PATCH)

    assert files == ["app.py"]
    assert (repository / "app.py").read_text(encoding="utf-8") == "return False\n"


def test_apply_patch_requires_explicit_approval(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    try:
        apply_patch(repository, VALID_PATCH, dry_run=False)
    except PatchApplicationError as exc:
        assert "explicit approval" in str(exc)
    else:
        raise AssertionError("Expected apply_patch to require approval")


def test_apply_patch_changes_file_after_approval(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    files = apply_patch(repository, VALID_PATCH, approved=True, dry_run=False)

    assert files == ["app.py"]
    assert (repository / "app.py").read_text(encoding="utf-8") == "return True\n"


def test_apply_patch_tool_is_blocked_through_registry(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    result = ToolRegistry(repository).execute("apply_patch", {"patch": VALID_PATCH})

    assert result.success is False
    assert "Mutation tools cannot be executed" in (result.error or "")
    assert (repository / "app.py").read_text(encoding="utf-8") == "return False\n"


def test_apply_patch_tool_blocks_mutation_through_registry(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    result = ToolRegistry(repository).execute(
        "apply_patch",
        {"patch": VALID_PATCH, "approved": True, "dry_run": False},
    )

    assert result.success is False
    assert "Mutation tools cannot be executed" in (result.error or "")
    assert (repository / "app.py").read_text(encoding="utf-8") == "return False\n"


CREATE_FILE_PATCH = """--- /dev/null
+++ b/new_module.py
@@ -0,0 +1,2 @@
+def created():
+    return True
"""


DELETE_FILE_PATCH = """--- a/app.py
+++ /dev/null
@@ -1 +0,0 @@
-return False
"""


def test_apply_patch_creates_file_after_approval(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    files = apply_patch(repository, CREATE_FILE_PATCH, approved=True, dry_run=False)

    assert files == ["new_module.py"]
    assert (repository / "new_module.py").read_text(encoding="utf-8") == "def created():\n    return True\n"


def test_apply_patch_deletes_file_after_approval(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    files = apply_patch(repository, DELETE_FILE_PATCH, approved=True, dry_run=False)

    assert files == ["app.py"]
    assert not (repository / "app.py").exists()


def test_apply_patch_rejection_leaves_repository_unchanged(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    original = (repository / "app.py").read_text(encoding="utf-8")

    try:
        apply_patch(repository, VALID_PATCH, dry_run=False)
    except PatchApplicationError:
        pass
    else:
        raise AssertionError("Expected apply_patch to require approval")

    assert (repository / "app.py").read_text(encoding="utf-8") == original
