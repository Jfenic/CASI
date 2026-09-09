"""Formatting helpers used by the initials task."""


def join_parts(parts: list[str]) -> str:
	"""Join non-empty parts with dots."""

	return ".".join(part for part in parts if part)
