def get_environments_v2_identity_override_document_key(
    feature_id: int | None = None,
    identity_uuid: str | None = None,
) -> str:
    if feature_id is None:
        if identity_uuid:
            raise ValueError(
                "Cannot generate identity override document key without feature_id"
            )
        return "identity_override:"
    if identity_uuid is None:
        return f"identity_override:{feature_id}:"
    return f"identity_override:{feature_id}:{identity_uuid}"
