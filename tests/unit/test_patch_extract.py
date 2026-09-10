from __future__ import annotations

from casi.patching.extract import extract_patch

VALID_PATCH = "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-return False\n+return True"


def test_extract_patch_reads_fenced_diff() -> None:
    response = f"```diff\n{VALID_PATCH}```"
    assert extract_patch(response) == f"{VALID_PATCH}\n"


def test_extract_patch_reads_fenced_diff_with_preamble() -> None:
    response = f"```diff\nAquí tienes el parche:\n{VALID_PATCH}```"
    assert extract_patch(response) == f"{VALID_PATCH}\n"


def test_extract_patch_removes_blank_line_after_hunk_header() -> None:
    response = (
        "```diff\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1 +1 @@\n"
        "\n"
        "-return False\n"
        "+return True\n"
        "```"
    )

    assert extract_patch(response) == f"{VALID_PATCH}\n"


def test_extract_patch_reads_raw_diff() -> None:
    response = f"Propuesta de corrección:\n{VALID_PATCH}"
    assert extract_patch(response) == f"{VALID_PATCH}\n"


def test_extract_patch_trims_trailing_prose() -> None:
    response = f"{VALID_PATCH}\n\nNo olvides ejecutar los tests."
    assert extract_patch(response) == f"{VALID_PATCH}\n"


def test_extract_patch_returns_none_without_headers() -> None:
    assert extract_patch("Error al validar el parche proporcionado.") is None


def test_extract_patch_finds_diff_embedded_in_json_text() -> None:
    response = (
        '{"type":"final","content":"Applied fix","patch":"--- '
        "a/app.py\\n+++ b/app.py\\n@@ -1 +1 @@\\n-return "
        'False\\n+return True"}'
    )
    assert extract_patch(response) == (
        "--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-return False\n+return True\n"
    )
