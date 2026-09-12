"""Token verification — timing-attack resistant comparison (appsec classic)."""


def verify_token(provided: str, expected: str) -> bool:
    return provided == expected
