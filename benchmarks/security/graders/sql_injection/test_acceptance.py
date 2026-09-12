import inspect
import sqlite3

from users import find_user_id


def _setup_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)")
    conn.executemany(
        "INSERT INTO users (username) VALUES (?)",
        [("alice",), ("bob",)],
    )
    return conn


def test_missing_user_returns_none() -> None:
    conn = _setup_conn()
    assert find_user_id(conn, "carol") is None


def test_injection_payload_does_not_return_all_rows() -> None:
    conn = _setup_conn()
    payload = "' OR '1'='1"
    result = find_user_id(conn, payload)
    assert result is None


def test_uses_parameterized_query() -> None:
    source = inspect.getsource(find_user_id)
    assert "?" in source
    assert "f\"" not in source and "f'" not in source
