from collections import defaultdict
from datetime import datetime, timedelta

from app_analytics.models import FeatureEvaluationRaw
from app_analytics.split_testing.helpers import gather_split_test_metrics
from app_analytics.split_testing.models import (
    ConversionEvent,
    ConversionEventType,
    SplitTest,
)
from django.conf import settings
from django.utils import timezone

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureStateValue
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

# TODO: This if-statement will be replaced with a separate
#       repository installation like LDAP.
if settings.USE_POSTGRES_FOR_ANALYTICS:

    @register_recurring_task(run_every=timedelta(minutes=15))
    def update_split_tests() -> None:
        # Code is placed in below private function for testing.
        return _update_split_tests()


def _update_split_tests() -> None:
    assert settings.USE_POSTGRES_FOR_ANALYTICS
    features = Feature.objects.filter(type=MULTIVARIATE)
    for feature in features:
        # Split the work into multiple tasks to avoid the time
        # limit on how long a task can run before being stale.
        update_features_split_tests.delay(
            kwargs={"feature_id": feature.id},
        )


@register_task_handler()
def update_features_split_tests(feature_id: int) -> None:
    assert settings.USE_POSTGRES_FOR_ANALYTICS

    feature = Feature.objects.get(id=feature_id)
    environment_ids = feature.feature_states.all().values_list(
        "environment_id", flat=True
    )

    qs_values_list = (
        FeatureEvaluationRaw.objects.filter(
            feature_name=feature.name,
            environment_id__in=environment_ids,
            identity_identifier__isnull=False,
            enabled_when_evaluated=True,  # Only evaluated features.
        )
        .values_list(
            "environment_id",
            "identity_identifier",
            "created_at",
        )
        .order_by("created_at")
    )

    environment_identifiers = defaultdict(dict)
    for environment_id, identity_identifier, created_at in qs_values_list:
        if identity_identifier in environment_identifiers[environment_id]:
            continue

        environment_identifiers[environment_id][identity_identifier] = created_at

    for (
        environment_id,
        evaluated_identity_identifiers,
    ) in environment_identifiers.items():
        for cet in ConversionEventType.objects.filter(environment_id=environment_id):
            _save_environment_split_test(
                feature=feature,
                environment_id=environment_id,
                evaluated_identity_identifiers=evaluated_identity_identifiers,
                conversion_event_type=cet,
            )


def _save_environment_split_test(
    feature: Feature,
    environment_id: int,
    evaluated_identity_identifiers: dict[str, datetime],
    conversion_event_type: ConversionEventType,
) -> None:
    environment = Environment.objects.get(id=environment_id)

    # Select related duplicate environment for get_hash_key call.
    evaluated_identities = Identity.objects.filter(
        environment_id=environment_id,
        identifier__in=evaluated_identity_identifiers,
    ).select_related("environment")

    feature_state = feature.feature_states.get(environment_id=environment_id)

    evaluation_counts = {}
    conversion_counts = {}

    for mv_option in feature.multivariate_options.all():
        evaluation_counts[mv_option.id] = 0
        conversion_counts[mv_option.id] = 0

    # For when falling back to the control group ie, FeatureStateValue.
    evaluation_counts[None] = 0
    conversion_counts[None] = 0

    # Only consider identities that have observed the evalauted
    # feature, since the conversion event can be viewed by others
    # who have not seen the feature at all, and thus out of scope.
    conversion_events = ConversionEvent.objects.filter(
        environment=environment,
        identity__in=evaluated_identities,
        type=conversion_event_type,
    )

    conversion_identities = {ce.identity: ce for ce in conversion_events}

    for evaluated_identity in evaluated_identities:
        identity_hash_key = evaluated_identity.get_hash_key(
            environment.use_identity_composite_key_for_hashing
        )
        mvfo = feature_state.get_multivariate_feature_state_value(identity_hash_key)

        # Use the null id for the control group.
        if isinstance(mvfo, FeatureStateValue):
            _id = None

        # Use the normal multivariate feature option id otherwise.
        else:
            _id = mvfo.id

        evaluation_counts[_id] += 1
        if evaluated_identity in conversion_identities:
            # Only include results if the feature was evaluated
            # before the conversion event.
            conversion_event = conversion_identities[evaluated_identity]
            evaluated_at = evaluated_identity_identifiers[evaluated_identity.identifier]
            if evaluated_at < conversion_event.created_at:
                conversion_counts[_id] += 1

    pvalue = gather_split_test_metrics(
        evaluation_counts,
        conversion_counts,
    )

    qs_existing_split_tests = SplitTest.objects.filter(
        conversion_event_type=conversion_event_type,
        feature=feature,
        environment=environment,
    )

    new_split_tests = []
    existing_split_tests = []
    for mv_feature_option_id, evaluation_count in evaluation_counts.items():
        conversion_count = conversion_counts[mv_feature_option_id]

        if mv_feature_option_id is None:
            existing_split_test = qs_existing_split_tests.filter(
                multivariate_feature_option_id__isnull=True
            ).first()
        else:
            existing_split_test = qs_existing_split_tests.filter(
                multivariate_feature_option_id=mv_feature_option_id
            ).first()

        if existing_split_test:
            existing_split_test.evaluation_count = evaluation_count
            existing_split_test.conversion_count = conversion_count
            existing_split_test.pvalue = pvalue
            existing_split_test.updated_at = timezone.now()

            existing_split_tests.append(existing_split_test)
            continue

        new_split_tests.append(
            SplitTest(
                conversion_event_type=conversion_event_type,
                environment=environment,
                feature=feature,
                multivariate_feature_option_id=mv_feature_option_id,
                evaluation_count=evaluation_count,
                conversion_count=conversion_count,
                pvalue=pvalue,
            )
        )

    SplitTest.objects.bulk_update(
        existing_split_tests,
        ["evaluation_count", "conversion_count", "pvalue", "updated_at"],
    )
    SplitTest.objects.bulk_create(new_split_tests)
