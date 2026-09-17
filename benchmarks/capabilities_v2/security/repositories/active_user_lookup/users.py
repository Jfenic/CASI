def lookup(conn, username):
    row = conn.execute(
        f"SELECT id FROM users WHERE username = '{username}' AND active = 1"
    ).fetchone()
    return row[0] if row else None
