from postfix import eval_postfix


def test_simple_addition() -> None:
    assert eval_postfix(["3", "4", "+"]) == 7
