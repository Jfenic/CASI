from reader import read_records


def test_records():
    assert read_records('{"id":1}\n\n{"id":2}') == [{"id": 1}, {"id": 2}]
