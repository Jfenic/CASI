"""Validate and normalize email addresses."""


def is_valid_email(email: str) -> bool:
	"""Return True when the address looks valid."""

	if not email:
		return False
	return "." in email
