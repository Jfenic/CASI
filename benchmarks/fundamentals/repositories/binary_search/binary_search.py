"""Binary search on a sorted sequence — classic algorithms exercise."""


def binary_search(items: list[int], target: int) -> int:
    left = 0
    right = len(items) - 1
    while left <= right:
        mid = (left + right) // 2
        value = items[mid]
        if value == target:
            return mid
        if value < target:
            left = mid + 1
        else:
            right = mid - 1
    return 0
