import sqlite3

from users import lookup


def test_injection():
    with sqlite3.connect(":memory:") as conn:
        conn.execute("CREATE TABLE users(id INTEGER, username TEXT, active INTEGER)")
        conn.execute("INSERT INTO users VALUES (1, 'alice', 1)")
        assert lookup(conn, "' OR 1=1 --") is None
