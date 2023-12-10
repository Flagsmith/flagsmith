from multimethod import overload

# TODO This might require type: ignores in the future, but it's just so nice!


@overload
def get_environments_v2_identity_override_document_key() -> str:
    return "identity_override:"


@overload
def get_environments_v2_identity_override_document_key(  # noqa: F811
    feature_id: int,
) -> str:
    return f"identity_override:{feature_id}:"


@overload
def get_environments_v2_identity_override_document_key(  # noqa: F811
    feature_id: int,
    identity_uuid: str,
) -> str:
    return f"identity_override:{feature_id}:{identity_uuid}"
