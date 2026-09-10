"""Validate email addresses."""


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    return "." in email
