"""Safety and applicability validation for unified patches."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from casi.config import settings
from casi.repository.security import is_sensitive_path, resolve_repository
from .diff_parser import is_relative_safe_path, parse_patch_files


@dataclass(frozen=True)
class PatchValidation:
	valid: bool
	files: list[str]
	error: str | None = None


def validate_patch(repository: str | Path, patch: str) -> PatchValidation:
	"""Validate patch safety and run Git's non-mutating applicability check."""

	if len(patch.encode("utf-8")) > settings.max_patch_size_bytes:
		return PatchValidation(False, [], "Patch exceeds the configured size limit")

	try:
		root = resolve_repository(repository)
		patch_files = parse_patch_files(patch)
	except (ValueError, OSError) as exc:
		return PatchValidation(False, [], str(exc))

	paths = [path.path for path in patch_files]
	if len(paths) > settings.max_patch_files:
		return PatchValidation(False, paths, "Patch modifies too many files")

	for path in paths:
		if not path or not is_relative_safe_path(path):
			return PatchValidation(False, paths, f"Unsafe patch path: {path}")
		if is_sensitive_path(Path(path)):
			return PatchValidation(False, paths, f"Sensitive patch path: {path}")

	check = subprocess.run(
		["git", "apply", "--check", "--whitespace=error-all", "-"],
		cwd=root,
		input=patch,
		capture_output=True,
		text=True,
		check=False,
	)
	if check.returncode != 0:
		return PatchValidation(False, paths, check.stderr.strip() or "Patch does not apply")

	return PatchValidation(True, paths)
