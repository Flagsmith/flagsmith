from organisations.chargebee.types import ChargebeeObjMetadata


def test_add_chargebee_object_meta_data():
    # Given
    a_obj_metadata = ChargebeeObjMetadata(seats=10, api_calls=100)
    another_obj_metadata = ChargebeeObjMetadata(seats=20, api_calls=200, projects=100)

    # When
    added_chargebee_obj_metadata = a_obj_metadata + another_obj_metadata

    # Then
    assert added_chargebee_obj_metadata.seats == 30
    assert added_chargebee_obj_metadata.api_calls == 300
    assert added_chargebee_obj_metadata.projects == 100
