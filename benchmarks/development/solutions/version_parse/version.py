"""Parse semantic version strings."""


def parse_version(text: str) -> tuple[int, int, int]:
    parts = text.split(".")
    if len(parts) != 3:
        raise ValueError("expected three dot-separated parts")
    try:
        return tuple(int(part) for part in parts)
    except ValueError as exc:
        raise ValueError("version parts must be integers") from exc
