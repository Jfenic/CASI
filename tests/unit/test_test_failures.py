from __future__ import annotations

from casi.agent.test_failures import extract_failure_paths


def test_extract_failure_paths_from_pytest_traceback() -> None:
    output = (
        "FAILED tests/test_sorter.py::test_bubble_sort_orders_ascending - AssertionError\n"
        "_______________________ test_bubble_sort_orders_ascending _______________________\n"
        "    def test_bubble_sort_orders_ascending():\n"
        ">       assert bubble_sort([2, 1]) == [1, 2]\n"
        "tests/test_sorter.py:6: AssertionError\n"
        "sorter.py:10: in bubble_sort\n"
        '  File "sorter.py", line 10, in bubble_sort\n'
    )

    assert extract_failure_paths(output) == [
        "tests/test_sorter.py",
        "sorter.py",
    ]
