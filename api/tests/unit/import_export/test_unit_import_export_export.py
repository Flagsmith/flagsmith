import json
import re

from core.constants import STRING
from django.core.serializers.json import DjangoJSONEncoder
from flag_engine.segments.constants import ALL_RULE

from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.workflows.core.models import ChangeRequest
from import_export.export import (
    export_environments,
    export_features,
    export_organisation,
    export_projects,
)
from integrations.amplitude.models import AmplitudeConfiguration
from integrations.datadog.models import DataDogConfiguration
from integrations.heap.models import HeapConfiguration
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.new_relic.models import NewRelicConfiguration
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.segment.models import SegmentConfiguration
from integrations.slack.models import SlackConfiguration, SlackEnvironment
from integrations.webhook.models import WebhookConfiguration
from organisations.invites.models import InviteLink
from organisations.models import (
    Organisation,
    OrganisationWebhook,
    Subscription,
)
from projects.models import Project
from projects.tags.models import Tag
from segments.models import EQUAL, Condition, Segment, SegmentRule


def test_export_organisation(db):
    # Given
    # an organisation
    organisation_name = "test org"
    organisation = Organisation.objects.create(name=organisation_name)

    # with a subscription
    Subscription.objects.create(
        organisation=organisation, max_seats=1, max_api_calls=50000
    )

    # and an invite link
    InviteLink.objects.create(organisation=organisation)

    # and a webhook
    OrganisationWebhook.objects.create(
        organisation=organisation, url="https://test.webhooks.com/"
    )

    # When
    export = export_organisation(organisation.id)

    # Then
    assert export

    # TODO: test whether the export is importable


def test_export_project(organisation):
    # Given
    # a project
    project_name = "test project"
    project = Project.objects.create(organisation=organisation, name=project_name)

    # a segment
    segment = Segment.objects.create(project=project, name="test segment")
    segment_rule = SegmentRule.objects.create(segment=segment, type=ALL_RULE)
    Condition(rule=segment_rule, operator=EQUAL, property="foo", value="bar")

    # a tag
    Tag.objects.create(label="tag", project=project, color="#000000")

    # and one of each of the integrations
    DataDogConfiguration.objects.create(project=project, api_key="api-key")
    NewRelicConfiguration.objects.create(project=project, api_key="api-key")
    SlackConfiguration.objects.create(project=project, api_token="api-token")

    # When
    export = export_projects(organisation.id)

    # Then
    assert export

    # TODO: test whether the export is importable


def test_export_environments(project):
    # Given
    # an environment
    environment_name = "test environment"
    environment = Environment.objects.create(project=project, name=environment_name)

    # an environment API key
    EnvironmentAPIKey.objects.create(environment=environment)

    # a wehbook
    Webhook.objects.create(environment=environment, url="https://test.webhook.com")

    # and one of each of all the integrations...
    AmplitudeConfiguration.objects.create(environment=environment, api_key="api-key")
    HeapConfiguration.objects.create(environment=environment, api_key="api-key")
    MixpanelConfiguration.objects.create(environment=environment, api_key="api-key")
    SegmentConfiguration.objects.create(environment=environment, api_key="api-key")
    RudderstackConfiguration.objects.create(environment=environment, api_key="api-key")
    WebhookConfiguration.objects.create(
        environment=environment, url="https://test.webhook.com"
    )
    slack_project_config = SlackConfiguration.objects.create(
        project=project, api_token="api-token"
    )
    SlackEnvironment.objects.create(
        environment=environment,
        slack_configuration=slack_project_config,
        channel_id="channel-id",
    )

    # When
    export = export_environments(project.organisation_id)

    # Then
    assert export

    # TODO: test whether the export is importable


def test_export_features(project, environment, segment, admin_user):
    # Given
    # a standard feature
    standard_feature = Feature.objects.create(project=project, name="standard_feature")
    standard_feature.owners.add(admin_user)

    # and a multivariate feature
    mv_feature = Feature.objects.create(
        project=project, name="mv_feature", type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type=STRING,
        string_value="foo",
    )

    # and a segment feature state
    feature_segment = FeatureSegment.objects.create(
        feature=standard_feature, segment=segment, environment=environment
    )
    FeatureState.objects.create(
        feature=standard_feature,
        feature_segment=feature_segment,
        environment=environment,
    )

    # and a feature state associated with a change request
    cr = ChangeRequest.objects.create(
        environment=environment, title="Test CR", user=admin_user
    )
    FeatureState.objects.create(
        feature=standard_feature, environment=environment, version=2, change_request=cr
    )

    # When
    export = export_features(organisation_id=project.organisation_id)

    # Then
    assert export

    json_export = json.dumps(export, cls=DjangoJSONEncoder)

    # verify that owners are not included in the export
    assert "owners" not in json_export

    # verify that change requests are not included in the export and that any feature
    # states associated with a change request are no longer associated with that CR.
    assert "workflows_core.changerequest" not in json_export
    assert not re.findall(r"\"change_request\": \[\"[a-z0-9\-]{36}\"\]", json_export)

    # TODO: test whether the export is importable
