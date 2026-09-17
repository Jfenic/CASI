import pytest
from archive import destination


@pytest.mark.parametrize("name", ["a/b.txt", "my file.txt", "a..b", "./a.txt"])
def test_safe_names(tmp_path, name):
    assert destination(tmp_path, name) == (tmp_path / name).resolve()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "name", ["", "../escape", "a/../../escape", "a/../b", "/tmp/outside"]
)
def test_rejects_names(tmp_path, name):
    with pytest.raises(ValueError):
        destination(tmp_path, name)


def test_symlink_escape_and_safe_link(tmp_path):
    root = tmp_path / "base"
    root.mkdir()
    outside = tmp_path / "base-other"
    outside.mkdir()
    (root / "escape").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        destination(root, "escape/file")
    (root / "inside").mkdir()
    (root / "safe").symlink_to(root / "inside", target_is_directory=True)
    assert destination(root, "safe/file") == root / "inside/file"
