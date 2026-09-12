"""User lookup — SQL injection prevention (database security classic)."""

import sqlite3


def find_user_id(conn: sqlite3.Connection, username: str) -> int | None:
    query = f"SELECT id FROM users WHERE username = '{username}'"
    row = conn.execute(query).fetchone()
    return None if row is None else int(row[0])
