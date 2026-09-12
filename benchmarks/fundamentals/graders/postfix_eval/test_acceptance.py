import pytest

from postfix import eval_postfix


@pytest.mark.parametrize(
    "tokens,expected",
    [
        (["3", "4", "+"], 7),
        (["8", "3", "2", "*", "-"], 2),
        (["5", "1", "2", "+", "4", "*", "+", "3", "-"], 14),
        (["12", "3", "/"], 4),
    ],
)
def test_eval_postfix(tokens, expected) -> None:
    assert eval_postfix(tokens) == expected
