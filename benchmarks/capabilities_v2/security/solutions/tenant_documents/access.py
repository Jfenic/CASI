from copy import deepcopy


def get_document(documents, tenant_id, user_id, document_id):
    document = documents[document_id]
    if document["tenant_id"] != tenant_id:
        raise PermissionError("access denied")
    if document["owner_id"] != user_id and not document["public"]:
        raise PermissionError("access denied")
    return deepcopy(document)
