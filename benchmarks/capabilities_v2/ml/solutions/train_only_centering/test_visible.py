from preprocessing import Centerer


def test_center():
    assert Centerer().fit([[1], [3]]).transform([[3]]) == [[1]]
