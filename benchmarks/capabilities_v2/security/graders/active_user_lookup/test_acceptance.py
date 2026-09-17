import sqlite3

import pytest
from users import lookup


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE users(id INTEGER, username TEXT, active INTEGER)")
    connection.executemany(
        "INSERT INTO users VALUES (?, ?, ?)",
        [
            (1, "alice", 1),
            (2, "O'Reilly", 1),
            (3, "' OR 1=1 --", 1),
            (4, "disabled", 0),
            (5, "José", 1),
        ],
    )
    yield connection
    connection.close()


@pytest.mark.parametrize(
    "name,expected",
    [
        ("alice", 1),
        ("O'Reilly", 2),
        ("' OR 1=1 --", 3),
        ("disabled", None),
        ("José", 5),
        ("missing", None),
        ("' OR 'x'='x", None),
        ("ALICE", None),
    ],
)
def test_exact_lookup(conn, name, expected):
    before = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
    assert lookup(conn, name) == expected
    assert conn.execute("SELECT * FROM users ORDER BY id").fetchall() == before


def test_bound_parameters():
    class RecordingConnection:
        def execute(self, sql, parameters=()):
            assert "O'Reilly" not in sql
            values = (
                list(parameters.values())
                if isinstance(parameters, dict)
                else list(parameters)
            )
            assert "O'Reilly" in values
            return self

        def fetchone(self):
            return (9,)

    assert lookup(RecordingConnection(), "O'Reilly") == 9
