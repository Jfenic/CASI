from summary import summarize


def test_mean_of_three_values() -> None:
    assert summarize([2, 4, 6]) == "mean=4.00"
