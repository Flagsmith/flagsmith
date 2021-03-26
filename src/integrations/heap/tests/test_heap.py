import pytest

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.heap.heap import HEAP_API_URL, HeapWrapper
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
def test_heap_when_generate_user_data_with_correct_values_then_success():
    # Given
    api_key = "123key"
    user_id = "user123"
    heap_wrapper = HeapWrapper(api_key=api_key)

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    environment_one = Environment.objects.create(
        name="Test Environment 1", project=project
    )
    feature = Feature.objects.create(name="Test Feature", project=project)
    feature_states = FeatureState.objects.filter(feature=feature)

    # When
    user_data = heap_wrapper.generate_user_data(
        user_id=user_id, feature_states=feature_states
    )

    # Then
    expected_user_data = {
        "app_id": api_key,
        "identity": user_id,
        "event": "Flagsmith Feature Flags",
        "properties": {"Test Feature": False},
    }
    assert expected_user_data == user_data
