def lookup(conn, username):
    row = conn.execute(
        "SELECT id FROM users WHERE username = ? AND active = 1", (username,)
    ).fetchone()
    return row[0] if row else None
