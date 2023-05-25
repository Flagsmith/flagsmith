from organisations.chargebee.tasks import update_chargebee_cache


def test_update_chargebee_cache(mocker):
    # Given
    mock_chargebee_cache = mocker.MagicMock()
    mocker.patch(
        "organisations.chargebee.tasks.ChargebeeCache",
        return_value=mock_chargebee_cache,
    )

    # When
    update_chargebee_cache()

    # Then
    mock_chargebee_cache.refresh.assert_called_once_with()
