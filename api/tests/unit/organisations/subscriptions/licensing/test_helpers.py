import json

from organisations.subscriptions.licensing.helpers import (
    sign_licence,
    verify_signature,
)


def test_sign_and_verify_signature_of_licence() -> None:
    # Given
    licence_content = {
        "organisation_name": "Test Organisation",
        "plan_id": "Enterprise",
        "num_seats": 20,
        "num_projects": 3,
        "num_api_calls": 3_000_000,
    }

    licence = json.dumps(licence_content)

    # When
    licence_signature = sign_licence(licence)
    signature_verification = verify_signature(licence, licence_signature)

    # Then
    assert licence_signature
    assert signature_verification is True
