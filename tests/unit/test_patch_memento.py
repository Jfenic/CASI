from __future__ import annotations

from pathlib import Path

import pytest

from casi.patching.memento import PatchMemento, PatchMementoStack


def test_patch_memento_captures_and_restores_modification(tmp_path: Path) -> None:
    app_file = tmp_path / "app.py"
    app_file.write_text("def run():\n    return False\n", encoding="utf-8")

    patch = (
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1,2 +1,2 @@\n"
        " def run():\n"
        "-    return False\n"
        "+    return True\n"
    )

    memento = PatchMemento.capture(tmp_path, patch, files=["app.py"])
    assert "app.py" in memento.snapshots
    assert memento.snapshots["app.py"] == b"def run():\n    return False\n"

    # Simulate patch applied
    app_file.write_text("def run():\n    return True\n", encoding="utf-8")
    assert app_file.read_text(encoding="utf-8") == "def run():\n    return True\n"

    # Restore
    restored = memento.restore(tmp_path)
    assert restored == ["app.py"]
    assert app_file.read_text(encoding="utf-8") == "def run():\n    return False\n"


def test_patch_memento_captures_and_restores_new_file(tmp_path: Path) -> None:
    new_file = tmp_path / "new_module.py"
    patch = "--- /dev/null\n+++ b/new_module.py\n@@ -0,0 +1 @@\n+# new file\n"

    memento = PatchMemento.capture(tmp_path, patch, files=["new_module.py"])
    assert memento.snapshots["new_module.py"] is None

    # Simulate new file created
    new_file.write_text("# new file\n", encoding="utf-8")
    assert new_file.exists()

    # Restore should delete the newly created file
    restored = memento.restore(tmp_path)
    assert restored == ["new_module.py"]
    assert not new_file.exists()


def test_patch_memento_stack_operations(tmp_path: Path) -> None:
    stack = PatchMementoStack()
    assert stack.is_empty()
    assert len(stack) == 0
    assert stack.peek() is None
    assert stack.pop() is None

    f1 = tmp_path / "f1.py"
    f1.write_text("v1", encoding="utf-8")
    m1 = PatchMemento.capture(tmp_path, "patch1", files=["f1.py"])
    stack.push(m1)

    assert not stack.is_empty()
    assert len(stack) == 1
    assert stack.peek() == m1

    f1.write_text("v2", encoding="utf-8")
    memento, restored = stack.undo(tmp_path)
    assert memento == m1
    assert restored == ["f1.py"]
    assert f1.read_text(encoding="utf-8") == "v1"
    assert stack.is_empty()

    with pytest.raises(ValueError, match="No patch memento available to undo"):
        stack.undo(tmp_path)


def test_patch_memento_stack_clear(tmp_path: Path) -> None:
    stack = PatchMementoStack()
    m = PatchMemento.capture(tmp_path, "dummy", files=[])
    stack.push(m)
    assert len(stack) == 1
    stack.clear()
    assert stack.is_empty()
