def redact(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower() in {"password", "token", "secret", "authorization"}
            else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
