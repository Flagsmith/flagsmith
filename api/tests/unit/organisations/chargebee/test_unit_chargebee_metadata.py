from organisations.chargebee.metadata import ChargebeeObjMetadata


def test_chargebee_obj_metadata__add_two_instances__sums_values():  # type: ignore[no-untyped-def]
    # Given
    a_obj_metadata = ChargebeeObjMetadata(seats=10, api_calls=100)
    another_obj_metadata = ChargebeeObjMetadata(seats=20, api_calls=200, projects=100)

    # When
    added_chargebee_obj_metadata = a_obj_metadata + another_obj_metadata

    # Then
    assert added_chargebee_obj_metadata.seats == 30
    assert added_chargebee_obj_metadata.api_calls == 300
    assert added_chargebee_obj_metadata.projects is None


def test_chargebee_obj_metadata__multiply_by_scalar__scales_values():  # type: ignore[no-untyped-def]
    # Given
    metadata = ChargebeeObjMetadata(seats=10, api_calls=100)

    # When
    new_metadata = metadata * 3

    # Then
    assert new_metadata.seats == 30
    assert new_metadata.api_calls == 300
    assert new_metadata.projects is None


def test_chargebee_obj_metadata__multiply_with_null_projects__keeps_null():  # type: ignore[no-untyped-def]
    # Given
    metadata = ChargebeeObjMetadata(seats=10, api_calls=100, projects=None)

    # When
    new_metadata = metadata * 3

    # Then
    assert new_metadata.seats == 30
    assert new_metadata.api_calls == 300
    assert new_metadata.projects is None
