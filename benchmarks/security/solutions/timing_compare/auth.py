"""Token verification — timing-attack resistant comparison (appsec classic)."""

import hmac


def verify_token(provided: str, expected: str) -> bool:
    return hmac.compare_digest(provided.encode(), expected.encode())
