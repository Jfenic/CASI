from binary_search import binary_search


def test_finds_existing_value() -> None:
    assert binary_search([1, 3, 5, 7], 5) == 2
