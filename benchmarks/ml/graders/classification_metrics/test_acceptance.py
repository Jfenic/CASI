from metrics import accuracy, f1_score, precision, recall


def test_mixed_predictions():
    y_true = [1, 0, 1, 0, 1, 0]
    y_pred = [1, 0, 0, 0, 1, 1]
    assert accuracy(y_true, y_pred) == 4 / 6
    assert precision(y_true, y_pred) == 2 / 3
    assert recall(y_true, y_pred) == 2 / 3
    assert abs(f1_score(y_true, y_pred) - 2 / 3) < 1e-9


def test_all_negative_predictions():
    y_true = [1, 1, 0, 0]
    y_pred = [0, 0, 0, 0]
    assert recall(y_true, y_pred) == 0.0
    assert precision(y_true, y_pred) == 0.0
    assert f1_score(y_true, y_pred) == 0.0


def test_empty_inputs():
    assert accuracy([], []) == 0.0
    assert precision([], []) == 0.0
    assert recall([], []) == 0.0
    assert f1_score([], []) == 0.0
