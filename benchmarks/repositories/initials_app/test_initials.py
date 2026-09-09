from initials import initials


def test_builds_initials_from_names() -> None:
	assert initials("Ada", "Lovelace") == "A.L."


def test_ignores_empty_parts() -> None:
	assert initials("Grace", "") == "G."
