import heapq


def build_order(graph):
    pending = {name: set(deps) for name, deps in graph.items()}
    for deps in graph.values():
        for name in deps:
            pending.setdefault(name, set())
    ready = [name for name, deps in pending.items() if not deps]
    heapq.heapify(ready)
    result = []
    while ready:
        name = heapq.heappop(ready)
        result.append(name)
        for other, deps in pending.items():
            if name in deps:
                deps.remove(name)
                if not deps:
                    heapq.heappush(ready, other)
    if len(result) != len(pending):
        raise ValueError("cycle")
    return result
