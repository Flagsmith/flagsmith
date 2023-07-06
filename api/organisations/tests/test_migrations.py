import pytest
from django.conf import settings


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_migration_creates_default_subscription_for_organisations_without_subscription(
    migrator,
):
    # Given
    # we use one of the dependencies of the migration we want to test to set the
    # initial state of the database correctly
    old_state = migrator.apply_initial_migration(
        ("organisations", "0035_add_organisation_subscription_information_cache")
    )

    old_organisation_model_class = old_state.apps.get_model(
        "organisations", "Organisation"
    )

    old_subscription_model_class = old_state.apps.get_model(
        "organisations", "Subscription"
    )

    # an organisation without subscription
    organisation_without_subscription = old_organisation_model_class.objects.create(
        name="Test Org Without subscription"
    )

    # Now, let's create another organisation
    subscription_id = "test-subscription-id"
    organisation_with_subscription = old_organisation_model_class.objects.create(
        name="Test Org With subscription"
    )
    # with a subscription id to mimic the behavior of existing organisations
    # that have a subscription
    existing_subscription = old_subscription_model_class.objects.create(
        organisation=organisation_with_subscription, subscription_id=subscription_id
    )
    # When
    # we apply the migration we want to test
    new_state = migrator.apply_tested_migration(
        ("organisations", "0037_add_default_subscription_to_existing_organisations")
    )

    new_subscription_model_class = new_state.apps.get_model(
        "organisations", "Subscription"
    )

    # Then
    # a new subscription was created for the organisation
    # that did not have a subscription
    assert new_subscription_model_class.objects.filter(
        organisation_id=organisation_without_subscription.id
    ).exists()

    # and old subscription still exists
    assert new_subscription_model_class.objects.filter(
        organisation_id=organisation_with_subscription.id,
        subscription_id=subscription_id,
        id=existing_subscription.id,
    ).exists()
