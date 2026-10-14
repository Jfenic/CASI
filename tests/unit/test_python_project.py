from pathlib import Path

from casi.agent.create_workflow import repository_has_test_files
from casi.repository.python_project import discover_test_files, python_source_roots


def test_test_discovery_uses_nested_and_configured_names(tmp_path: Path) -> None:
    checks = tmp_path / "checks" / "nested"
    checks.mkdir(parents=True)
    (checks / "cart_test.py").write_text("")
    assert discover_test_files(tmp_path) == ["checks/nested/cart_test.py"]
    (tmp_path / "pytest.ini").write_text("[pytest]\npython_files = check_*.py\n")
    (checks / "check_cart.py").write_text("")
    assert discover_test_files(tmp_path) == ["checks/nested/check_cart.py"]
    assert repository_has_test_files(tmp_path, require_actual_files=True)


def test_testpaths_filters_unrelated_files(tmp_path: Path) -> None:
    checks = tmp_path / "checks"
    checks.mkdir()
    (checks / "test_cart.py").write_text("")
    (tmp_path / "test_example.py").write_text("")
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = checks\n")
    assert discover_test_files(tmp_path) == ["checks/test_cart.py"]


def test_source_roots_honor_package_configuration_and_reject_external_paths(
    tmp_path: Path,
) -> None:
    library = tmp_path / "library"
    library.mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[tool.setuptools.package-dir]\n"" = "library"\n'
        '[tool.pytest.ini_options]\npythonpath = ["../", ".env"]\n'
    )
    assert python_source_roots(tmp_path) == [library, tmp_path]
