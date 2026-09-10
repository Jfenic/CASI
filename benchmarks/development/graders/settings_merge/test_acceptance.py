from copy import deepcopy

from settings import merge_settings


def test_no_aliases_or_mutations():
    defaults = {"db": {"ports": [1], "flags": {"a": True}}, "extra": [{"x": 1}]}
    overrides = {"db": {"name": "main"}, "custom": [{"y": 2}]}
    before = (deepcopy(defaults), deepcopy(overrides))
    result = merge_settings(defaults, overrides)
    assert (defaults, overrides) == before
    result["db"]["ports"].append(2)
    result["db"]["flags"]["a"] = False
    result["extra"][0]["x"] = 3
    result["custom"][0]["y"] = 4
    assert (defaults, overrides) == before


def test_replacements():
    assert merge_settings(
        {"a": {"x": 1}, "b": [1], "c": 2}, {"a": None, "b": [2], "c": {"y": 3}}
    ) == {"a": None, "b": [2], "c": {"y": 3}}
