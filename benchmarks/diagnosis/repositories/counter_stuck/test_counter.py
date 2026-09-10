from counter import Counter


def test_increment_twice() -> None:
    counter = Counter()
    counter.increment()
    counter.increment()
    assert counter.value() == 2
