"""Sample library used for read-only benchmark tasks."""


def slugify(text: str) -> str:
	return text.strip().lower().replace(" ", "-")


def excerpt(text: str, limit: int = 40) -> str:
	if len(text) <= limit:
		return text
	return text[: limit - 3] + "..."
