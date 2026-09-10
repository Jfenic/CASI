from metrics import accuracy, precision, recall


def test_mixed_predictions():
    y_true = [1, 0, 1, 0]
    y_pred = [1, 0, 0, 1]
    assert accuracy(y_true, y_pred) == 0.5
    assert precision(y_true, y_pred) == 0.5
    assert recall(y_true, y_pred) == 0.5
