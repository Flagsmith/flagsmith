# Generated by Django 4.2.15 on 2024-10-29 11:11
import logging

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from organisations.subscriptions.constants import SubscriptionPlanFamily


def update_limits(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    subscription_model = apps.get_model("organisations", "Subscription")
    organisation_subscription_information_cache_model = apps.get_model(
        "organisations", "OrganisationSubscriptionInformationCache"
    )

    all_paid_subscriptions = subscription_model.objects.select_related(
        "organisation", "organisation__subscription_information_cache"
    ).exclude(plan="free")

    cache_models_to_update = []

    for subscription in all_paid_subscriptions:
        subscription_family = SubscriptionPlanFamily.get_by_plan_id(subscription.plan)
        if subscription_family != SubscriptionPlanFamily.ENTERPRISE:
            # We only want to update Enterprise plans since:
            #  1. start up and scale up should only have the defaults
            #  2. scale up plans are handled differently (using the VERSIONING_RELEASE_DATE setting) which
            #     is needed to avoid having to create another plan in chargebee.
            continue

        if (osic := getattr(subscription.organisation, "subscription_information_cache", None)) is None:
            continue

        osic.audit_log_visibility_days = osic.feature_history_visibility_days = None
        cache_models_to_update.append(osic)

    organisation_subscription_information_cache_model.objects.bulk_update(
        cache_models_to_update,
        fields=["audit_log_visibility_days", "feature_history_visibility_days"]
    )


class Migration(migrations.Migration):

    dependencies = [
        ("organisations", "0057_limit_audit_and_version_history"),
    ]

    operations = [
        migrations.RunPython(update_limits, reverse_code=migrations.RunPython.noop),
    ]