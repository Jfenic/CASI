import pytest
from archive import destination


def test_traversal(tmp_path):
    with pytest.raises(ValueError):
        destination(tmp_path, "../outside")
