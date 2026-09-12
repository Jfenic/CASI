from queue import Queue


def test_fifo_order() -> None:
    queue = Queue()
    queue.enqueue("a")
    queue.enqueue("b")
    assert queue.dequeue() == "a"
