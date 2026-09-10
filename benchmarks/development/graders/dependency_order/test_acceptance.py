from copy import deepcopy

import pytest
from dependencies import build_order


def test_ready_queue_and_implicit_nodes():
    graph = {"a": ["b", "b"], "z": [], "d": ["c"]}
    before = deepcopy(graph)
    assert build_order(graph) == ["b", "a", "c", "d", "z"]
    assert graph == before


def test_diamond():
    assert build_order({"d": ["b", "c"], "b": ["a"], "c": ["a"]}) == [
        "a",
        "b",
        "c",
        "d",
    ]
    assert build_order({}) == []


@pytest.mark.parametrize(
    "graph", [{"a": ["a"]}, {"a": ["b"], "b": ["a"]}, {"z": [], "a": ["b"], "b": ["a"]}]
)
def test_cycles(graph):
    with pytest.raises(ValueError):
        build_order(graph)
