"""Discover Python source and test files from repository configuration."""

from __future__ import annotations

import configparser
import fnmatch
import shlex
import tomllib
from pathlib import Path

from casi.exceptions import SecurityError
from casi.repository.explorer import list_files
from casi.repository.security import safe_path


def load_pyproject(repository: Path) -> dict:
    try:
        return tomllib.loads(
            safe_path(repository, "pyproject.toml").read_text(encoding="utf-8")
        )
    except (OSError, ValueError, UnicodeError, SecurityError):
        return {}


def pytest_options(repository: Path) -> dict:
    """Read supported pytest configuration without importing project code."""

    for name, section in (
        ("pytest.ini", "pytest"),
        (".pytest.ini", "pytest"),
        ("pyproject.toml", ""),
        ("tox.ini", "pytest"),
        ("setup.cfg", "tool:pytest"),
    ):
        if name == "pyproject.toml":
            options = load_pyproject(repository).get("tool", {}).get("pytest", {})
            if "ini_options" in options:
                return options["ini_options"]
            continue
        parser = configparser.ConfigParser(interpolation=None)
        try:
            parser.read_string(safe_path(repository, name).read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError, configparser.Error, SecurityError):
            continue
        if parser.has_section(section):
            return dict(parser[section])
    return {}


def _option_list(value: object) -> list[str]:
    if isinstance(value, str):
        try:
            return shlex.split(value)
        except ValueError:
            return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def python_source_roots(repository: Path) -> list[Path]:
    """Return existing import roots inside the repository."""

    project = load_pyproject(repository)
    setuptools = project.get("tool", {}).get("setuptools", {})
    configured = _option_list(pytest_options(repository).get("pythonpath", []))
    configured += list(setuptools.get("package-dir", {}).values())
    packages = setuptools.get("packages", {})
    if isinstance(packages, dict):
        configured += _option_list(packages.get("find", {}).get("where", []))
    hatch_packages = (
        project.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
        .get("packages", [])
    )
    configured += [str(Path(path).parent) for path in _option_list(hatch_packages)]
    roots: list[Path] = []
    for relative in [*configured, ".", "src"]:
        try:
            root = safe_path(repository, relative)
        except SecurityError:
            continue
        if root.is_dir() and root not in roots:
            roots.append(root)
    return roots


def discover_test_files(repository: Path) -> list[str]:
    """Find safe test files using pytest's configured filename patterns."""

    options = pytest_options(repository)
    patterns = _option_list(options.get("python_files", ["test_*.py", "*_test.py"]))
    roots: list[Path] = []
    for pattern in _option_list(options.get("testpaths", [])):
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            continue
        for path in repository.glob(pattern):
            try:
                root = safe_path(repository, path)
            except SecurityError:
                continue
            if root.exists():
                roots.append(root)
    return [
        path.as_posix()
        for path in list_files(repository)
        if any(fnmatch.fnmatchcase(path.name, pattern) for pattern in patterns)
        and (
            not roots or any((repository / path).is_relative_to(root) for root in roots)
        )
    ]
