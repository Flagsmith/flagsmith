from app_analytics.models import FeatureEvaluationRaw
from app_analytics.split_testing.models import ConversionEvent, SplitTest
from app_analytics.split_testing.tasks import _update_split_tests
from pytest_django.fixtures import SettingsWrapper

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from projects.models import Project


def test_update_split_tests(
    settings: SettingsWrapper,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True

    feature1 = Feature.objects.create(
        name="1",
        project=project,
        initial_value="200",
        is_server_key_only=True,
        default_enabled=True,
    )
    feature2 = Feature.objects.create(
        name="2",
        project=project,
        initial_value="banana",
        default_enabled=False,
    )

    MultivariateFeatureOption.objects.create(
        feature=feature1,
        default_percentage_allocation=30,
        type=STRING,
        string_value="mv_feature_option1",
    )
    MultivariateFeatureOption.objects.create(
        feature=feature1,
        default_percentage_allocation=70,
        type=STRING,
        string_value="mv_feature_option2",
    )
    MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=50,
        type=STRING,
        string_value="mv_feature_option3",
    )
    MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=50,
        type=STRING,
        string_value="mv_feature_option4",
    )

    identity1 = Identity.objects.create(
        identifier="test-identity-1", environment=environment
    )
    identity2 = Identity.objects.create(
        identifier="test-identity-2", environment=environment
    )
    identity3 = Identity.objects.create(
        identifier="test-identity-3", environment=environment
    )
    identity4 = Identity.objects.create(
        identifier="test-identity-4", environment=environment
    )

    # Create evaluation for both features for identity1
    FeatureEvaluationRaw.objects.create(
        feature_name=feature1.name,
        environment_id=environment.id,
        evaluation_count=2,
        identifier=identity1.identifier,
    )
    FeatureEvaluationRaw.objects.create(
        feature_name=feature2.name,
        environment_id=environment.id,
        evaluation_count=1,
        identifier=identity1.identifier,
    )

    # Create evaluation for only feature2 for identity2
    FeatureEvaluationRaw.objects.create(
        feature_name=feature2.name,
        environment_id=environment.id,
        evaluation_count=1,
        identifier=identity2.identifier,
    )

    # Create evaluation for only feature2 for identity3
    FeatureEvaluationRaw.objects.create(
        feature_name=feature2.name,
        environment_id=environment.id,
        evaluation_count=1,
        identifier=identity3.identifier,
    )

    # Create duplicate evaluations for only feature1 for identity4
    FeatureEvaluationRaw.objects.create(
        feature_name=feature1.name,
        environment_id=environment.id,
        evaluation_count=1,
        identifier=identity4.identifier,
    )
    FeatureEvaluationRaw.objects.create(
        feature_name=feature1.name,
        environment_id=environment.id,
        evaluation_count=1,
        identifier=identity4.identifier,
    )

    # Create conversion events for identity3 and identity 4
    ConversionEvent.objects.create(
        environment=environment,
        identity=identity3,
    )

    ConversionEvent.objects.create(
        environment=environment,
        identity=identity4,
    )

    # When
    _update_split_tests()

    # Then
    split_tests = SplitTest.objects.all()
    assert len(split_tests) == 4
    assert sum([st.evaluation_count for st in split_tests]) == 5
    assert sum([st.conversion_count for st in split_tests]) == 2
    for st in split_tests:
        assert st.pvalue == 1.0
        assert st.statistic == 0.0
