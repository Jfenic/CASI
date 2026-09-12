import pytest

from safe_path import safe_join


def test_rejects_parent_segments(tmp_path) -> None:
    base = tmp_path / "public"
    base.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("private")
    with pytest.raises(ValueError):
        safe_join(str(base), "../secret.txt")


def test_rejects_absolute_paths(tmp_path) -> None:
    base = tmp_path / "public"
    base.mkdir()
    with pytest.raises(ValueError):
        safe_join(str(base), str(tmp_path / "outside.txt"))


def test_nested_relative_stays_inside(tmp_path) -> None:
    base = tmp_path / "public"
    nested = base / "docs"
    nested.mkdir(parents=True)
    result = safe_join(str(base), "docs/report.txt")
    assert result.startswith(str(base.resolve()))
    assert result.endswith("report.txt")
