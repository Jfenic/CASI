from normalize import standardize


def test_zero_mean_unit_scale():
    rows = [[0.0, 10.0], [2.0, 14.0], [4.0, 18.0]]
    result = standardize(rows)
    for col in range(2):
        column = [row[col] for row in result]
        assert abs(sum(column) / len(column)) < 1e-9
