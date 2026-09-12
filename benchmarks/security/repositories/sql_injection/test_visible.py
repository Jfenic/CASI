import sqlite3

from users import find_user_id


def test_finds_existing_user() -> None:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE users (id INTEGER, username TEXT)")
    conn.execute("INSERT INTO users VALUES (1, 'alice')")
    assert find_user_id(conn, "alice") == 1
