"""Extract unified diffs from model responses."""

from __future__ import annotations

import json
import re

_FENCE_MARKERS = ("```diff", "```patch", "```")
_DIFF_HEADER = re.compile(r"(?:^|\n)--- ", re.MULTILINE)
_PATCH_JSON_KEYS = ("patch", "diff", "unified_diff", "unifiedDiff")
_FINAL_JSON_KEYS = ("content", "response", "message", "answer", "text", "assistant")


def extract_patch(response: str) -> str | None:
	"""Extract a fenced or raw unified diff from model output."""

	text = response.replace("\r\n", "\n").replace("\r", "\n")

	for marker in _FENCE_MARKERS:
		search_from = 0
		while True:
			remainder = text[search_from:]
			index = remainder.find(marker)
			if index < 0:
				break
			start = search_from + index + len(marker)
			end = text.find("```", start)
			if end < 0:
				break
			patch = _extract_diff_from_text(text[start:end])
			if patch is not None:
				return patch
			search_from = start

	patch = _extract_diff_from_text(text)
	if patch is not None:
		return patch
	return _extract_patch_from_json_payload(text)


def _extract_patch_from_json_payload(text: str) -> str | None:
	"""Recover diffs stored in separate JSON fields or escaped content strings."""

	stripped = text.strip()
	if not stripped.startswith("{"):
		return None

	try:
		payload = json.loads(stripped)
	except json.JSONDecodeError:
		return None
	if not isinstance(payload, dict):
		return None

	candidates: list[str] = []
	for key in _PATCH_JSON_KEYS:
		value = payload.get(key)
		if isinstance(value, str) and value.strip():
			candidates.append(value)
	for key in _FINAL_JSON_KEYS:
		value = payload.get(key)
		if isinstance(value, str) and value.strip():
			candidates.append(value)

	for candidate in candidates:
		patch = _extract_diff_from_text(candidate)
		if patch is not None:
			return patch
	return None


def _extract_diff_from_text(text: str) -> str | None:
	match = _DIFF_HEADER.search(text)
	if match is None:
		return None

	start = match.start()
	if start > 0 and text[start] == "\n":
		start += 1

	patch = text[start:].strip()
	if "+++ " not in patch:
		return None

	patch = _trim_trailing_prose(patch)
	if not patch:
		return None
	return patch.strip() + "\n"


def _trim_trailing_prose(patch: str) -> str:
	"""Drop trailing prose that sometimes follows an otherwise valid diff."""

	lines = patch.splitlines()
	trimmed: list[str] = []
	saw_hunk = False

	for line in lines:
		if line.startswith("@@"):
			saw_hunk = True
		if saw_hunk and not line:
			# Small local models commonly insert a visual blank line between
			# the hunk header and its first diff line. It is not valid unified
			# diff syntax, so discard it instead of truncating the whole patch.
			continue
		if saw_hunk and line and not _is_diff_line(line):
			break
		trimmed.append(line)

	return "\n".join(trimmed).strip()


def _is_diff_line(line: str) -> bool:
	return line.startswith(("--- ", "+++ ", "@@", "+", "-", " ", "\\", "diff --git"))
