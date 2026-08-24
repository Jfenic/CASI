"""Extract unified diffs from model responses."""

from __future__ import annotations


def extract_patch(response: str) -> str | None:
	"""Extract a fenced or raw unified diff from model output."""

	marker = "```diff"
	if marker in response:
		patch = response.split(marker, 1)[1].split("```", 1)[0].strip()
		if patch.startswith("--- ") and "+++ " in patch:
			return patch + "\n"

	start = response.find("--- a/")
	if start >= 0:
		patch = response[start:].strip()
		if "+++ b/" in patch:
			return patch + "\n"
	return None
