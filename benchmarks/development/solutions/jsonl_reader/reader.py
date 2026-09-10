import json


def read_records(text):
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"line {number}: invalid JSON") from exc
        if not isinstance(value, dict):
            raise ValueError(f"line {number}: expected object")
        records.append(value)
    return records
