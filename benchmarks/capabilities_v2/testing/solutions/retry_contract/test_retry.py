import pytest
from retrying import retry


def test_eventual_success():
    calls = []

    def operation():
        calls.append(1)
        if len(calls) < 2:
            raise RuntimeError("temporary")
        return 42

    assert retry(operation, 3) == 42
    assert len(calls) == 2


def test_exhaustion():
    calls = []

    def operation():
        calls.append(1)
        raise RuntimeError("failure")

    with pytest.raises(RuntimeError):
        retry(operation, 2)
    assert len(calls) == 2


def test_other_error():
    calls = []

    def operation():
        calls.append(1)
        raise TypeError("bad")

    with pytest.raises(TypeError):
        retry(operation)
    assert len(calls) == 1


@pytest.mark.parametrize("attempts", [0, -1])
def test_invalid_attempts(attempts):
    calls = []
    with pytest.raises(ValueError):
        retry(lambda: calls.append(1), attempts)
    assert calls == []


def test_default_attempts_and_final_exception():
    errors = [RuntimeError(str(i)) for i in range(3)]
    calls = []

    def operation():
        index = len(calls)
        calls.append(index)
        raise errors[index]

    with pytest.raises(RuntimeError) as caught:
        retry(operation)
    assert len(calls) == 3
    assert caught.value is errors[-1]


def test_single_attempt():
    calls = []

    def operation():
        calls.append(1)
        raise RuntimeError("once")

    with pytest.raises(RuntimeError):
        retry(operation, 1)
    assert len(calls) == 1


def test_first_success_has_no_extra_calls():
    calls = []

    def operation():
        calls.append(1)
        return None

    assert retry(operation) is None
    assert len(calls) == 1
