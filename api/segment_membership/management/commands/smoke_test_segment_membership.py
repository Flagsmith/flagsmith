"""Smoke-test the segment membership pipeline against a local DynamoDB
+ a real Snowflake account configured via SNOWFLAKE_* env vars.

The command:

1. Creates the EdgeIdentities table in the configured DynamoDB endpoint.
2. Seeds a project, environment, and segment in core Postgres if missing.
3. Seeds identities in Dynamo whose traits match the segment predicate
   (and an equal number that don't).
4. Runs `backfill_identities_to_snowflake()` synchronously.
5. Runs `refresh_project_segment_counts(project_id)` synchronously.
6. Asserts the resulting `SegmentMembership.count` equals the number of
   matching identities seeded.

`is_membership_enabled` is patched to True for the run so the
Flagsmith-on-Flagsmith flag isn't required.

Usage:

    AWS_ENDPOINT_URL_DYNAMODB=http://localhost:8000 \
    IDENTITIES_TABLE_NAME_DYNAMO=flagsmith_smoke_identities \
    AWS_ACCESS_KEY_ID=local AWS_SECRET_ACCESS_KEY=local AWS_DEFAULT_REGION=us-east-1 \
    poetry run python manage.py smoke_test_segment_membership
"""

import logging
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership import services as membership_services
from segment_membership import tasks as membership_tasks
from segment_membership.models import SegmentMembership
from segment_membership.tasks import (
    backfill_identities_to_snowflake,
    refresh_project_segment_counts,
)
from segments.models import Condition, Segment, SegmentRule

logger = logging.getLogger(__name__)

PROJECT_NAME = "smoke-test-segment-membership"
ENV_NAME = "smoke-env"
SEGMENT_NAME = "growth-plan-users"
TRAIT_KEY = "plan"
MATCH_VALUE = "growth"
NON_MATCH_VALUE = "basic"
N_PER_BUCKET = 25  # 25 matches + 25 non-matches = 50 total


class Command(BaseCommand):
    help = "End-to-end smoke test for segment membership against DynamoDB Local + Snowflake."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--keep",
            action="store_true",
            help="Skip Snowflake row cleanup at the end.",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        if not settings.IDENTITIES_TABLE_NAME_DYNAMO:
            raise CommandError("IDENTITIES_TABLE_NAME_DYNAMO must be set")
        if not membership_services.is_snowflake_configured():
            raise CommandError("SNOWFLAKE_* settings must be populated")

        org, project, environment, segment = _ensure_fixtures()
        self.stdout.write(
            f"fixtures: project={project.id} env={environment.id} segment={segment.id}"
        )

        table_name = _ensure_dynamo_table()
        self.stdout.write(f"dynamo table ready: {table_name}")

        _seed_identities(environment.api_key)
        self.stdout.write(
            f"seeded {N_PER_BUCKET} matching + {N_PER_BUCKET} non-matching identities"
        )

        with (
            patch.object(
                membership_services, "is_membership_enabled", return_value=True
            ),
            patch.object(membership_tasks, "is_membership_enabled", return_value=True),
        ):
            backfill_identities_to_snowflake()
            self.stdout.write("backfill complete")

            refresh_project_segment_counts(project.id)
            self.stdout.write("refresh complete")

        with membership_services.open_snowflake_session() as sess:
            sess.query_tag = "flagsmith:segment_membership:smoke_test:diag"
            total = sess.sql(
                "SELECT COUNT(*) AS c FROM IDENTITIES WHERE environment_id = ?",
                params=[environment.api_key],
            ).collect()[0]["C"]
            self.stdout.write(f"snowflake IDENTITIES rows for env: {total}")
            sample = sess.sql(
                "SELECT identifier, traits FROM IDENTITIES WHERE environment_id = ? LIMIT 1",
                params=[environment.api_key],
            ).collect()
            self.stdout.write(f"sample row: {sample}")
            self.stdout.write(
                f"live segments: {list(Segment.live_objects.filter(project=project).values_list('id', 'name'))}"
            )
            sess.query_tag = "flagsmith:segment_membership:smoke_test:diag"
            results = membership_services.compute_segment_counts_for_project(
                project, sess
            )
            self.stdout.write(f"compute_segment_counts_for_project: {results}")

        try:
            membership = SegmentMembership.objects.get(
                segment=segment, environment=environment
            )
            self.stdout.write(
                f"SegmentMembership: count={membership.count} last_synced_at={membership.last_synced_at}"
            )
            if membership.count != N_PER_BUCKET:
                raise CommandError(
                    f"Expected count={N_PER_BUCKET}, got {membership.count}"
                )
        except SegmentMembership.DoesNotExist:
            raise CommandError(
                "SegmentMembership row not created — see diagnostics above"
            )
        self.stdout.write(self.style.SUCCESS("✓ Counts match expected"))

        if not options["keep"]:
            _cleanup_snowflake(environment.api_key)
            self.stdout.write("snowflake rows cleaned up")


def _ensure_fixtures() -> tuple[Organisation, Project, Environment, Segment]:
    org, _ = Organisation.objects.get_or_create(name="smoke-test")
    project, _ = Project.objects.get_or_create(name=PROJECT_NAME, organisation=org)
    environment, _ = Environment.objects.get_or_create(name=ENV_NAME, project=project)
    segment, created = Segment.objects.get_or_create(
        name=SEGMENT_NAME,
        project=project,
        defaults={"description": "smoke-test segment"},
    )
    if created or not segment.rules.exists():
        # ALL > ANY > condition tree mirroring how the dashboard builds segments.
        outer = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        inner = SegmentRule.objects.create(rule=outer, type=SegmentRule.ANY_RULE)
        Condition.objects.create(
            rule=inner,
            property=TRAIT_KEY,
            operator="EQUAL",
            value=MATCH_VALUE,
        )
    return org, project, environment, segment


def _ensure_dynamo_table() -> str:
    name = settings.IDENTITIES_TABLE_NAME_DYNAMO
    client = boto3.client("dynamodb")
    try:
        client.describe_table(TableName=name)
        client.delete_table(TableName=name)
        client.get_waiter("table_not_exists").wait(TableName=name)
    except client.exceptions.ResourceNotFoundException:
        pass

    client.create_table(
        TableName=name,
        KeySchema=[{"AttributeName": "composite_key", "KeyType": "HASH"}],
        AttributeDefinitions=[
            {"AttributeName": "composite_key", "AttributeType": "S"},
            {"AttributeName": "environment_api_key", "AttributeType": "S"},
            {"AttributeName": "identifier", "AttributeType": "S"},
            {"AttributeName": "identity_uuid", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "environment_api_key-identifier-index",
                "KeySchema": [
                    {"AttributeName": "environment_api_key", "KeyType": "HASH"},
                    {"AttributeName": "identifier", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "identity_uuid-index",
                "KeySchema": [
                    {"AttributeName": "identity_uuid", "KeyType": "HASH"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    client.get_waiter("table_exists").wait(TableName=name)
    return name


def _seed_identities(env_api_key: str) -> None:
    table = boto3.resource("dynamodb").Table(settings.IDENTITIES_TABLE_NAME_DYNAMO)
    now = datetime.now(timezone.utc).isoformat()
    with table.batch_writer() as batch:
        for i in range(N_PER_BUCKET):
            for value, label in ((MATCH_VALUE, "match"), (NON_MATCH_VALUE, "no")):
                identifier = f"{label}-{i}"
                batch.put_item(
                    Item={
                        "composite_key": f"{env_api_key}_{identifier}",
                        "environment_api_key": env_api_key,
                        "identifier": identifier,
                        "identity_uuid": str(uuid.uuid4()),
                        "created_date": now,
                        "identity_traits": [
                            {"trait_key": TRAIT_KEY, "trait_value": value},
                        ],
                    }
                )


def _cleanup_snowflake(env_api_key: str) -> None:
    with membership_services.open_snowflake_session() as sess:
        sess.query_tag = "flagsmith:segment_membership:smoke_test:cleanup"
        sess.sql(
            "DELETE FROM IDENTITIES WHERE environment_id = ?",
            params=[env_api_key],
        ).collect()
