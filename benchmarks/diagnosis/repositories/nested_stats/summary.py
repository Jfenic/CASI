"""Summarize a batch of measurements."""

from normalize import normalize
from report import format_report


def summarize(values: list[float]) -> str:
    normalized = normalize(values)
    return format_report(normalized)
