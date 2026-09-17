from encoding import Encoder


def test_first_seen():
    assert Encoder().fit(["z", "a"]).transform(["z"]) == [[1, 0]]
