from pathlib import Path

import pytest

from casi_code_agent.exceptions import BinaryFileError
from casi_code_agent.repository.reader import read_file


def test_reader_adds_line_numbers(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    target = repository / "notes.txt"
    target.write_text("alpha\nbeta\n", encoding="utf-8")

    result = read_file(repository, "notes.txt", start_line=1, end_line=2)

    assert result == "1: alpha\n2: beta"


def test_binary_file_is_rejected(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    target = repository / "blob.bin"
    target.write_bytes(b"\x00\x01\x02binary")

    with pytest.raises(BinaryFileError):
        read_file(repository, "blob.bin")
