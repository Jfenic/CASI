from copy import deepcopy

import pytest
from access import get_document


@pytest.mark.parametrize(
    "tenant,user,public,allowed",
    [
        ("a", "owner", False, True),
        ("a", "other", False, False),
        ("a", "other", True, True),
        ("b", "owner", False, False),
        ("b", "owner", True, False),
        ("b", "other", True, False),
    ],
)
def test_authorization(tenant, user, public, allowed):
    docs = {"d": {"tenant_id": "a", "owner_id": "owner", "public": public, "data": [1]}}
    before = deepcopy(docs)
    if allowed:
        result = get_document(docs, tenant, user, "d")
        assert result == docs["d"]
        result["data"].append(2)
    else:
        with pytest.raises(PermissionError):
            get_document(docs, tenant, user, "d")
    assert docs == before


def test_missing():
    with pytest.raises(KeyError):
        get_document({}, "a", "u", "missing")
