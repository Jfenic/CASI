"""Controlled application of validated unified patches."""

from __future__ import annotations

import subprocess
from pathlib import Path

from casi.patching.validator import validate_patch


class PatchApplicationError(ValueError):
	"""Raised when a validated patch cannot be applied."""


def apply_patch(
	repository: str | Path,
	patch: str,
	*,
	approved: bool = False,
	dry_run: bool = True,
) -> list[str]:
	"""Validate and optionally apply a patch after explicit approval."""

	validation = validate_patch(repository, patch)
	if not validation.valid:
		raise PatchApplicationError(validation.error or "Patch is invalid")
	if not approved and not dry_run:
		raise PatchApplicationError("Patch application requires explicit approval")
	if dry_run:
		return validation.files

	root = Path(repository).expanduser().resolve()
	result = subprocess.run(
		["git", "apply", "--whitespace=error-all", "-"],
		cwd=root,
		input=patch,
		capture_output=True,
		text=True,
		check=False,
	)
	if result.returncode != 0:
		raise PatchApplicationError(result.stderr.strip() or "Patch application failed")
	return validation.files
