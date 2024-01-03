from collections import defaultdict
from datetime import timedelta

from app_analytics.models import FeatureEvaluationRaw
from app_analytics.split_testing.helpers import gather_split_test_metrics
from app_analytics.split_testing.models import ConversionEvent, SplitTest
from django.conf import settings

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature
from task_processor.decorators import register_recurring_task

if settings.USE_POSTGRES_FOR_ANALYTICS:

    @register_recurring_task(run_every=timedelta(minutes=15))
    def update_split_tests() -> None:
        # Code is placed in below private function for testing.
        return _update_split_tests()


def _update_split_tests() -> None:
    assert settings.USE_POSTGRES_FOR_ANALYTICS

    features = Feature.objects.filter(
        type=MULTIVARIATE,
    ).prefetch_related("feature_states", "multivariate_options")

    for feature in features:
        environment_ids = feature.feature_states.all().values_list(
            "environment_id", flat=True
        )

        qs_values_list = FeatureEvaluationRaw.objects.filter(
            feature_name=feature.name,
            environment_id__in=environment_ids,
            identifier__isnull=False,
        ).values_list("environment_id", "identifier")

        # Eliminate duplicate identifiers
        qs_values_list = qs_values_list.distinct()

        environment_identifiers = defaultdict(list)
        for env_identifier in qs_values_list:
            environment_id, identifier = env_identifier
            environment_identifiers[environment_id].append(identifier)

        for environment_id, identifiers in environment_identifiers.items():
            _save_environment_split_test(
                feature=feature,
                environment_id=environment_id,
                identifiers=identifiers,
            )


def _save_environment_split_test(
    feature: Feature, environment_id: int, identifiers: list[str]
) -> None:
    environment = Environment.objects.get(id=environment_id)
    identities = Identity.objects.filter(
        environment_id=environment_id,
        identifier__in=identifiers,
    )
    feature_state = feature.feature_states.get(environment_id=environment_id)

    evaluation_counts = {}
    conversion_counts = {}

    for mv_option in feature.multivariate_options.all():
        evaluation_counts[mv_option.id] = 0
        conversion_counts[mv_option.id] = 0

    conversion_events = ConversionEvent.objects.filter(
        environment=environment,
        identity__in=identities,
    )

    conversion_identities = set(
        Identity.objects.filter(conversion_events__in=conversion_events)
    )

    for identity in identities:
        identity_hash_key = identity.get_hash_key(
            environment.use_identity_composite_key_for_hashing
        )
        mvfo = feature_state.get_multivariate_feature_state_value(identity_hash_key)
        evaluation_counts[mvfo.id] += 1
        if identity in conversion_identities:
            conversion_counts[mvfo.id] += 1

    pvalue, statistic = gather_split_test_metrics(
        evaluation_counts,
        conversion_counts,
    )

    # Delete all the former split tests to avoid stale MV options.
    SplitTest.objects.filter(
        feature=feature,
        environment=environment,
    ).delete()

    split_tests = []
    for mv_feature_option_id, evaluation_count in evaluation_counts.items():
        conversion_count = conversion_counts[mv_feature_option_id]
        split_tests.append(
            SplitTest(
                environment=environment,
                feature=feature,
                multivariate_feature_option_id=mv_feature_option_id,
                evaluation_count=evaluation_count,
                conversion_count=conversion_count,
                pvalue=pvalue,
                statistic=statistic,
            )
        )

    SplitTest.objects.bulk_create(split_tests)
