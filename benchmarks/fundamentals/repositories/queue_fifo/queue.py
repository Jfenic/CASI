"""Queue (FIFO) — classic data-structure exercise."""


class Queue:
    def __init__(self) -> None:
        self._items: list[object] = []

    def enqueue(self, item: object) -> None:
        self._items.append(item)

    def dequeue(self) -> object:
        if not self._items:
            raise IndexError("dequeue from empty queue")
        return self._items.pop()

    def is_empty(self) -> bool:
        return len(self._items) == 0
