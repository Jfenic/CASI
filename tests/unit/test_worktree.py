"""Comprehensive unit tests for WorktreeManager and WorktreeSession."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from casi.sandbox.base import TestResult
from casi.sandbox.docker_runner import DockerRunner, DockerTestRunner
from casi.workspace.worktree import (
    WorktreeManager,
    WorktreeMutationError,
)


def _init_git_repo(path: Path) -> str:
    """Initialize a git repository with an initial commit and return the commit SHA."""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "CASI Test"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@casi.local"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    (path / "file1.txt").write_text("initial content\n", encoding="utf-8")
    (path / "src").mkdir()
    (path / "src" / "app.py").write_text(
        "def hello(): return 'hello'\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=path,
        check=True,
        capture_output=True,
    )
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def test_worktree_manager_initialization(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    assert manager.repository_path == repo.resolve()
    assert manager.worktree_base == (repo / ".casi" / "worktrees").resolve()
    assert manager.is_git_repository() is True
    assert manager.is_detached_head() is False
    assert manager.get_head_commit() is not None


def test_worktree_manager_custom_worktree_dir(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    custom_wt = tmp_path / "custom_worktrees"

    manager = WorktreeManager(repo, worktree_dir=custom_wt)
    assert manager.worktree_base == custom_wt.resolve()


def test_create_git_worktree_detached(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-001", detach=True)

    assert session.task_id == "task-001"
    assert session.is_git is True
    assert session.base_commit == base_commit
    assert session.branch_name is None
    assert session.active is True
    assert session.path.is_dir()
    assert (session.path / "file1.txt").is_file()
    assert (session.path / "file1.txt").read_text(
        encoding="utf-8"
    ) == "initial content\n"

    # Verify tracked in manager
    assert manager.get_worktree("task-001") is session
    assert session in manager.list_worktrees()

    # Clean up
    session.cleanup()
    assert session.active is False
    assert not session.path.exists()
    assert manager.get_worktree("task-001") is None


def test_create_git_worktree_with_ephemeral_branch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base_commit = _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-002", create_branch=True)

    assert session.is_git is True
    assert session.branch_name == "casi/wt-task-002"
    assert session.base_commit == base_commit

    # Verify branch was created in git
    res = subprocess.run(
        ["git", "branch", "--list", "casi/wt-task-002"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "casi/wt-task-002" in res.stdout

    # Clean up and verify branch pruned
    session.cleanup()
    assert not session.path.exists()
    res_after = subprocess.run(
        ["git", "branch", "--list", "casi/wt-task-002"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "casi/wt-task-002" not in res_after.stdout


def test_create_worktree_main_repo_in_detached_head(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    commit_sha = _init_git_repo(repo)

    # Detach HEAD in the main repository
    subprocess.run(
        ["git", "checkout", "--detach", commit_sha],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    manager = WorktreeManager(repo)
    assert manager.is_detached_head() is True

    session = manager.create_worktree("task-detached")
    assert session.is_git is True
    assert session.base_commit == commit_sha
    assert (session.path / "src" / "app.py").is_file()

    session.cleanup()
    assert not session.path.exists()


def test_non_git_repository_fallback(tmp_path: Path) -> None:
    repo = tmp_path / "non_git_repo"
    repo.mkdir()
    (repo / "calc.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_calc.py").write_text(
        "def test_add(): pass\n", encoding="utf-8"
    )

    manager = WorktreeManager(repo)
    assert manager.is_git_repository() is False

    session = manager.create_worktree("task-fallback")
    assert session.is_git is False
    assert session.base_commit is None
    assert session.path.is_dir()
    assert (session.path / "calc.py").read_text(
        encoding="utf-8"
    ) == "def add(a, b): return a + b\n"
    assert (session.path / "tests" / "test_calc.py").is_file()

    # Stage mutations in non-git fallback
    session.write_file("calc.py", "def add(a, b): return a + b + 1\n")
    session.write_file("new_module.py", "CONSTANT = 42\n")

    diff = session.get_diff()
    assert "--- a/calc.py" in diff
    assert "+++ b/calc.py" in diff
    assert "new_module.py" in diff

    stats = session.get_diff_stats()
    assert any(s.path == "calc.py" for s in stats)
    assert any(s.path == "new_module.py" for s in stats)

    session.cleanup()
    assert not session.path.exists()


def test_empty_git_repository_fallback(tmp_path: Path) -> None:
    repo = tmp_path / "empty_git_repo"
    repo.mkdir()
    # Initialize empty git repo with no commits
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")

    manager = WorktreeManager(repo)
    assert manager.is_git_repository() is False  # No commits yet

    session = manager.create_worktree("task-empty")
    assert session.is_git is False
    assert (session.path / "README.md").read_text(encoding="utf-8") == "# Project\n"
    session.cleanup()


def test_multi_file_mutation_and_isolation(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-multi")

    # Mutate multiple files inside worktree
    session.write_file("file1.txt", "modified content\n", stage=True)
    session.write_file("src/new_service.py", "class Service:\n    pass\n", stage=True)
    session.delete_file("src/app.py", stage=True)

    # Verify files inside worktree
    assert session.read_file("file1.txt") == "modified content\n"
    assert session.read_file("src/new_service.py") == "class Service:\n    pass\n"
    assert not session.file_exists("src/app.py")

    # CRITICAL: Verify main repository is completely untouched!
    assert (repo / "file1.txt").read_text(encoding="utf-8") == "initial content\n"
    assert not (repo / "src" / "new_service.py").exists()
    assert (repo / "src" / "app.py").is_file()

    # Check diff extraction
    diff = session.get_diff()
    assert "diff --git a/file1.txt b/file1.txt" in diff
    assert "-initial content" in diff
    assert "+modified content" in diff
    assert "src/new_service.py" in diff
    assert "src/app.py" in diff

    # Diff stats
    stats = session.get_diff_stats()
    paths = {s.path for s in stats}
    assert "file1.txt" in paths
    assert "src/new_service.py" in paths
    assert "src/app.py" in paths

    changed = session.get_changed_files()
    assert "file1.txt" in changed
    assert "src/new_service.py" in changed
    assert "src/app.py" in changed

    session.cleanup()


def test_stage_files_batch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    with manager.create_worktree("task-batch", auto_cleanup=True) as session:
        session.stage_files(
            {
                "module_a.py": "def a(): pass\n",
                "module_b.py": "def b(): pass\n",
            }
        )
        assert session.file_exists("module_a.py")
        assert session.file_exists("module_b.py")

        diff = session.get_diff()
        assert "module_a.py" in diff
        assert "module_b.py" in diff


def test_apply_patch_inside_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    with manager.create_worktree("task-patch", auto_cleanup=True) as session:
        patch = (
            "diff --git a/file1.txt b/file1.txt\n"
            "--- a/file1.txt\n"
            "+++ b/file1.txt\n"
            "@@ -1 +1 @@\n"
            "-initial content\n"
            "+patched content\n"
        )
        files = session.apply_patch(patch)
        assert files == ["file1.txt"]
        assert session.read_file("file1.txt") == "patched content\n"
        # User's main repo untouched
        assert (repo / "file1.txt").read_text(encoding="utf-8") == "initial content\n"


def test_apply_invalid_patch_raises_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    with manager.create_worktree("task-invalid-patch", auto_cleanup=True) as session:
        with pytest.raises(WorktreeMutationError):
            session.apply_patch("garbage diff that cannot apply")


def test_review_and_apply_to_main_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-review")
    session.write_file("file1.txt", "updated for production\n", stage=True)

    # Test review prompt helper
    approved, saved = session.review(input_fn=lambda _: "y")
    assert approved is True
    assert saved is None

    # Refuse application without approval flag
    with pytest.raises(WorktreeMutationError, match="explicit human approval"):
        session.apply_to_main_repo(approved=False)

    # Apply with approval
    applied_files = session.apply_to_main_repo(approved=True)
    assert "file1.txt" in applied_files
    assert (repo / "file1.txt").read_text(
        encoding="utf-8"
    ) == "updated for production\n"

    session.cleanup()


def test_reset_discards_mutations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-reset")
    session.write_file("file1.txt", "bad mutation\n", stage=True)
    session.write_file("temporary.py", "untracked\n", stage=True)

    assert session.read_file("file1.txt") == "bad mutation\n"
    session.reset()

    # After reset, file1.txt restored and temporary.py gone
    assert session.read_file("file1.txt") == "initial content\n"
    assert not session.file_exists("temporary.py")
    assert session.get_diff() == ""

    session.cleanup()


def test_docker_runner_integration(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    mock_runner = MagicMock(spec=DockerRunner)
    mock_runner.run_in_workspace.return_value = TestResult(
        command=["pytest"],
        exit_code=0,
        stdout="1 passed",
        stderr="",
        duration_seconds=0.5,
    )

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-docker")

    res, runner_kind = session.run_tests(
        command=["pytest", "-q"],
        runner=mock_runner,
    )

    assert runner_kind == "docker"
    assert res.exit_code == 0
    mock_runner.run_in_workspace.assert_called_once_with(
        session.path,
        ["pytest", "-q"],
        timeout_seconds=120,
    )

    # Test DockerTestRunner alias and run_in_worktree
    assert DockerTestRunner is DockerRunner
    runner = DockerTestRunner()
    runner.is_available = MagicMock(return_value=True)  # type: ignore[method-assign]
    runner.run_in_workspace = MagicMock(  # type: ignore[method-assign]
        return_value=TestResult(
            command=["test"], exit_code=0, stdout="", stderr="", duration_seconds=0.1
        )
    )
    worktree_res = runner.run_in_worktree(session.path, ["pytest"])
    assert worktree_res.exit_code == 0
    runner.run_in_workspace.assert_called_once_with(
        session.path, ["pytest"], timeout_seconds=120
    )

    session.cleanup()


def test_cleanup_all_and_manager_context(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    with WorktreeManager(repo) as manager:
        s1 = manager.create_worktree("task-a")
        s2 = manager.create_worktree("task-b")
        assert len(manager.list_worktrees()) == 2
        assert s1.path.exists()
        assert s2.path.exists()

    # Upon manager context exit, cleanup_all was called
    assert not s1.path.exists()
    assert not s2.path.exists()
    assert len(manager.list_worktrees()) == 0


def test_security_and_path_validation(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)

    # Invalid task IDs
    with pytest.raises(ValueError, match="Invalid task_id"):
        manager.create_worktree("../escaped")
    with pytest.raises(ValueError, match="Invalid task_id"):
        manager.create_worktree("foo/bar")
    with pytest.raises(ValueError, match="non-empty string"):
        manager.create_worktree("")

    session = manager.create_worktree("task-sec")

    # Path traversal within worktree
    with pytest.raises(ValueError, match="Path must be relative"):
        session.write_file("/etc/passwd", "content")
    with pytest.raises(ValueError, match="Path traversal detected"):
        session.write_file("../../outside.txt", "content")

    # Sensitive paths within worktree
    with pytest.raises(ValueError, match="Sensitive path not allowed"):
        session.write_file(".env", "SECRET=1")
    with pytest.raises(ValueError, match="Sensitive path not allowed"):
        session.write_file(".git/config", "exploit")

    # Inactive session mutations
    session.cleanup()
    with pytest.raises(WorktreeMutationError, match="no longer active"):
        session.write_file("foo.py", "bar")
    with pytest.raises(WorktreeMutationError, match="no longer active"):
        session.delete_file("foo.py")


def test_worktree_recreate_same_task_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    s1 = manager.create_worktree("task-reuse")
    s1.write_file("file1.txt", "mutation 1\n", stage=True)

    # Creating with same task_id should clean up s1 and create fresh s2
    s2 = manager.create_worktree("task-reuse")
    assert s1.active is False
    assert s2.active is True
    assert s2.read_file("file1.txt") == "initial content\n"
    s2.cleanup()


def test_fallback_delete_and_diff(tmp_path: Path) -> None:
    repo = tmp_path / "non_git_repo"
    repo.mkdir()
    (repo / "item1.txt").write_text("item1\n", encoding="utf-8")
    (repo / "item2.txt").write_text("item2\n", encoding="utf-8")

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-fallback-del")
    session.delete_file("item2.txt")

    diff = session.get_diff()
    assert "deleted file mode 100644" in diff
    assert "item2.txt" in diff
    session.cleanup()


def test_diff_empty_when_no_changes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    with manager.create_worktree("task-nochange", auto_cleanup=True) as session:
        assert session.get_diff() == ""
        assert session.get_diff_stats() == []
        assert session.get_changed_files() == []


def test_binary_file_in_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    with manager.create_worktree("task-bin", auto_cleanup=True) as session:
        target = session.write_file("data.bin", b"\x00\xff\xfe\xfd", stage=True)
        assert target.read_bytes() == b"\x00\xff\xfe\xfd"


def test_remove_dirty_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-dirty")
    # Dirty worktree with untracked file
    (session.path / "untracked.txt").write_text("garbage", encoding="utf-8")

    # Force remove should clean it completely
    manager.remove_worktree("task-dirty")
    assert not session.path.exists()
    assert manager.get_worktree("task-dirty") is None


def test_task_id_validation_edge_cases(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    manager = WorktreeManager(repo)

    for invalid in [".", "-", "..", "...", ".hidden", "-task", "task-", "task..1", ""]:
        with pytest.raises(ValueError):
            manager.create_worktree(invalid)


def test_safe_path_rejects_empty_and_root_and_traversal(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-safe-path")

    with pytest.raises(ValueError, match="Path must be a non-empty relative path"):
        session.write_file("", "text")
    with pytest.raises(ValueError, match="Path traversal detected"):
        session.write_file(".", "text")
    with pytest.raises(ValueError, match="Path must be a non-empty relative path"):
        session.delete_file("")
    with pytest.raises(ValueError, match="Path traversal detected"):
        session.delete_file(".")
    with pytest.raises(ValueError, match="Path traversal detected"):
        session.delete_file("dir/../..")

    session.cleanup()


def test_delete_file_missing_ok_and_not_found(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-del-missing")

    with pytest.raises(FileNotFoundError, match="File not found in worktree"):
        session.delete_file("nonexistent.txt", missing_ok=False)

    # missing_ok=True should not raise
    session.delete_file("nonexistent.txt", missing_ok=True)
    session.cleanup()


def test_stale_git_worktree_registration_recovery(tmp_path: Path) -> None:
    import shutil

    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    s1 = manager.create_worktree("task-stale")
    assert s1.is_git is True
    # Simulate an abrupt crash: delete worktree folder without git worktree remove
    shutil.rmtree(s1.path)

    # Recovery without falling back to copy workspace
    manager2 = WorktreeManager(repo)
    s2 = manager2.create_worktree("task-stale")
    assert s2.is_git is True
    assert (s2.path / "file1.txt").is_file()
    s2.cleanup()


def test_existing_user_branch_not_deleted_on_cleanup(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    # Create a user branch
    subprocess.run(
        ["git", "branch", "user-feature"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    manager = WorktreeManager(repo)
    session = manager.create_worktree(
        "task-branch-preserve", branch="user-feature", create_branch=False
    )
    assert session.is_git is True
    assert session.branch_name == "user-feature"
    assert session.is_ephemeral_branch is False

    # Cleanup must NOT delete user-feature branch
    session.cleanup()
    res = subprocess.run(
        ["git", "branch", "--list", "user-feature"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "user-feature" in res.stdout


def test_non_git_diff_missing_newline_at_eof(tmp_path: Path) -> None:
    repo = tmp_path / "non_git_repo"
    repo.mkdir()
    (repo / "both_no_nl.txt").write_text("orig line")
    (repo / "orig_no_nl.txt").write_text("orig line")
    (repo / "mod_no_nl.txt").write_text("orig line\n")
    (repo / "del_no_nl.txt").write_text("to delete")

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-diff-nl")

    session.write_file("both_no_nl.txt", "mod line")
    session.write_file("orig_no_nl.txt", "mod line\n")
    session.write_file("mod_no_nl.txt", "mod line")
    session.write_file("new_no_nl.txt", "brand new")
    session.delete_file("del_no_nl.txt")

    diff = session.get_diff()
    assert "\\ No newline at end of file" in diff

    # Verify that git apply accepts the generated diff without "corrupt patch" errors
    res = subprocess.run(
        ["git", "apply", "--check", "-"],
        cwd=repo,
        input=diff,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"git apply --check failed: {res.stderr}\nDiff:\n{diff}"
    session.cleanup()


def test_git_submodule_worktree_support(tmp_path: Path) -> None:
    sub_origin = tmp_path / "sub_origin"
    sub_origin.mkdir()
    _init_git_repo(sub_origin)

    main_repo = tmp_path / "main_repo"
    main_repo.mkdir()
    _init_git_repo(main_repo)

    subprocess.run(
        [
            "git",
            "-c",
            "protocol.file.allow=always",
            "submodule",
            "add",
            str(sub_origin),
            "submod",
        ],
        cwd=main_repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "add submodule"],
        cwd=main_repo,
        check=True,
        capture_output=True,
    )

    submodule_path = main_repo / "submod"
    assert (
        submodule_path / ".git"
    ).is_file()  # submodule .git is a file, not a directory

    manager = WorktreeManager(submodule_path)
    assert manager.is_git_repository() is True

    session = manager.create_worktree("task-submod")
    assert session.is_git is True
    session.write_file("file1.txt", "submodule mutation\n", stage=True)
    diff = session.get_diff()
    assert "file1.txt" in diff
    assert "submodule mutation" in diff
    session.cleanup()
    assert not session.path.exists()


def test_apply_to_main_repo_wraps_patch_application_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    manager = WorktreeManager(repo)
    session = manager.create_worktree("task-conflict")
    session.write_file("file1.txt", "worktree change\n", stage=True)

    # In main repo, create conflicting change
    (repo / "file1.txt").write_text("conflicting main repo change\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "file1.txt"], cwd=repo, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "commit", "-m", "conflict"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    with pytest.raises(WorktreeMutationError):
        session.apply_to_main_repo(approved=True)

    session.cleanup()


def test_prune_orphaned_ephemeral_branches(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    # Manually create an orphaned casi/wt-* branch
    subprocess.run(
        ["git", "branch", "casi/wt-orphaned"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    manager = WorktreeManager(repo)
    # Active session with branch
    s_active = manager.create_worktree("task-active", create_branch=True)
    assert "casi/wt-task-active" == s_active.branch_name

    # Prune should delete casi/wt-orphaned but keep casi/wt-task-active
    manager.prune()

    res = subprocess.run(
        ["git", "branch", "--list", "casi/wt-*"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "casi/wt-orphaned" not in res.stdout
    assert "casi/wt-task-active" in res.stdout

    s_active.cleanup()


def test_live_docker_runner_in_worktree(tmp_path: Path) -> None:
    runner = DockerRunner()
    if not runner.is_available():
        pytest.skip("Docker is not available")

    repo = tmp_path / "docker_repo"
    repo.mkdir()
    _init_git_repo(repo)
    (repo / "test_sample.py").write_text(
        "def test_ok(): assert 2 + 2 == 4\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "add test"], cwd=repo, check=True, capture_output=True
    )

    manager = WorktreeManager(repo)
    with manager.create_worktree("task-docker-live", auto_cleanup=True) as session:
        result = runner.run_in_worktree(session.path, ["pytest", "-q"])
        assert result.exit_code == 0
        assert "1 passed" in result.stdout
