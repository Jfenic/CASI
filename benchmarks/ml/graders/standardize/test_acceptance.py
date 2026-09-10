from normalize import standardize


def test_sample_standard_deviation():
    rows = [[1.0, 4.0], [3.0, 8.0], [5.0, 12.0]]
    result = standardize(rows)
    assert result[0][0] == -1.0
    assert result[1][0] == 0.0
    assert result[2][0] == 1.0


def test_constant_feature_becomes_zero():
    rows = [[5.0, 1.0], [5.0, 3.0], [5.0, 5.0]]
    result = standardize(rows)
    assert result == [[0.0, -1.0], [0.0, 0.0], [0.0, 1.0]]


def test_does_not_mutate_input():
    rows = [[1.0, 2.0], [3.0, 4.0]]
    original = [row[:] for row in rows]
    _ = standardize(rows)
    assert rows == original
