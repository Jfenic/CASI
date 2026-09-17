import pytest
from access import get_document


def test_other_tenant():
    with pytest.raises(PermissionError):
        get_document(
            {"d": {"tenant_id": "a", "owner_id": "u", "public": True}}, "b", "u", "d"
        )
