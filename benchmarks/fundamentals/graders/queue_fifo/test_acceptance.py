import pytest

from queue import Queue


def test_fifo_dequeue_order() -> None:
    queue = Queue()
    for label in ("first", "second", "third"):
        queue.enqueue(label)
    assert queue.dequeue() == "first"
    assert queue.dequeue() == "second"
    assert queue.dequeue() == "third"
    assert queue.is_empty()


def test_empty_queue_raises() -> None:
    queue = Queue()
    with pytest.raises(IndexError):
        queue.dequeue()
