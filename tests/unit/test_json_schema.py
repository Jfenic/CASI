from __future__ import annotations

from casi.agent.create_workflow import repository_has_test_files
from casi.llm.json_schema import json_schema_type, normalize_json_schema_type


def test_json_schema_type_maps_python_types() -> None:
    assert json_schema_type(int) == "integer"
    assert json_schema_type(str) == "string"
    assert json_schema_type((str, int)) == "string"


def test_normalize_json_schema_type_fixes_legacy_names() -> None:
    assert normalize_json_schema_type("int") == "integer"
    assert normalize_json_schema_type("str | Path") == "string"


def test_repository_has_test_files_detects_pytest_layout(tmp_path) -> None:
    assert repository_has_test_files(tmp_path) is False
    (tmp_path / "test_sample.py").write_text("def test_ok():\n    assert True\n")
    assert repository_has_test_files(tmp_path) is True
