import pytest

from util.engine_models.identities.models import IdentityModel


@pytest.mark.parametrize(
    "django_id, use_identity_composite_key_for_hashing, expected_hash_key",
    [
        (None, True, "api-key_identifier"),
        (1, True, "api-key_identifier"),
        (1, False, "1"),
        (None, False, "identifier"),
    ],
)
def test_identity_model_get_hash_key__django_id_and_hashing_setting__returns_expected_key(
    django_id: int | None,
    use_identity_composite_key_for_hashing: bool,
    expected_hash_key: str,
) -> None:
    # Given
    identity_model = IdentityModel(
        identifier="identifier",
        environment_api_key="api-key",
        django_id=django_id,
    )

    # When
    hash_key = identity_model.get_hash_key(use_identity_composite_key_for_hashing)

    # Then
    assert hash_key == expected_hash_key
