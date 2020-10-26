from integrations.amplitude.amplitude import AmplitudeWrapper, AMPLITUDE_API_URL


def test_amplitude_initialized_correctly():
    # Given
    api_key = '123key'

    # When initialized
    amplitude_wrapper = AmplitudeWrapper(api_key=api_key)

    # Then
    expected_url = f"{AMPLITUDE_API_URL}/identify"
    assert amplitude_wrapper.url == expected_url
