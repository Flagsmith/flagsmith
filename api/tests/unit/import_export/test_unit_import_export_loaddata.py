"""
Tests to confirm that Django's `loaddata` works with the output of
`dumporganisationtolocalfs` for distributing feature flag changes
to a separate Flagsmith installation.

See: https://github.com/Flagsmith/flagsmith/issues/6760
"""

import json
import typing
import uuid

import pytest
from django.core.management import call_command
from django.core.serializers.base import DeserializationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.utils import IntegrityError
from flag_engine.segments.constants import ALL_RULE, EQUAL

from core.constants import STRING
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment, EnvironmentAPIKey, Webhook
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from import_export.export import full_export
from integrations.datadog.models import DataDogConfiguration
from integrations.heap.models import HeapConfiguration
from organisations.invites.models import InviteLink
from organisations.models import Organisation, OrganisationWebhook, Subscription
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule


def _dump_and_load(data: typing.List[dict]) -> None:  # type: ignore[type-arg]
    """Write export data to a temp file and load it via Django's loaddata."""
    file_path = f"/tmp/{uuid.uuid4()}.json"
    with open(file_path, "w") as f:
        f.write(json.dumps(data, cls=DjangoJSONEncoder))
    call_command("loaddata", file_path, format="json")


# ================================================================
# Roundtrip tests: export → loaddata into same DB (upsert behaviour)
# ================================================================


def test_full_export_loaddata_roundtrip__core_models(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
    segment: Segment,
):
    """Full export can be loaded into a database where the same objects
    already exist (matched by natural key), confirming the basic
    roundtrip works for core models that have get_by_natural_key."""
    # Given
    tag = Tag.objects.create(label="test-tag", project=project, color="#000000")
    feature.tags.add(tag)

    segment_rule = SegmentRule.objects.create(segment=segment, type=ALL_RULE)
    Condition.objects.create(
        rule=segment_rule, operator=EQUAL, property="plan", value="enterprise"
    )

    InviteLink.objects.create(organisation=organisation)
    OrganisationWebhook.objects.create(
        organisation=organisation, url="https://hooks.example.com/"
    )
    Webhook.objects.create(environment=environment, url="https://env.hooks.example.com")

    # Capture natural keys before export
    org_uuid = organisation.uuid
    project_uuid = project.uuid
    env_api_key = environment.api_key
    feature_uuid = feature.uuid
    segment_uuid = segment.uuid

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then - objects still exist with the same natural keys
    assert Organisation.objects.filter(uuid=org_uuid).exists()
    assert Project.objects.filter(uuid=project_uuid).exists()
    assert Environment.objects.filter(api_key=env_api_key).exists()
    assert Feature.objects.filter(uuid=feature_uuid).exists()
    assert Segment.objects.filter(uuid=segment_uuid).exists()
    assert Tag.objects.filter(uuid=tag.uuid).exists()

    # Verify no duplicates were created
    assert Organisation.objects.filter(uuid=org_uuid).count() == 1
    assert Project.objects.filter(uuid=project_uuid).count() == 1
    assert Environment.objects.filter(api_key=env_api_key).count() == 1
    assert Feature.objects.filter(uuid=feature_uuid).count() == 1


# ================================================================
# Incremental update tests: modify data, re-export, re-load
# ================================================================


def test_full_export_loaddata__incremental_feature_flag_update(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    """After an initial load, changing a feature flag value and re-loading
    correctly updates the value on the target."""
    # Given - initial load
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Capture the initial feature state value
    fs = FeatureState.objects.get(
        feature=feature, environment=environment, identity=None, feature_segment=None
    )
    initial_fsv = fs.feature_state_value
    assert initial_fsv.string_value != "updated_value"

    # When - update the feature state value and re-export/load
    initial_fsv.string_value = "updated_value"
    initial_fsv.save()

    updated_data = full_export(organisation.id)
    _dump_and_load(updated_data)

    # Then - the feature state value is updated
    fs.refresh_from_db()
    fs.feature_state_value.refresh_from_db()
    assert fs.feature_state_value.string_value == "updated_value"


def test_full_export_loaddata__incremental_new_feature(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    """After an initial load, adding a new feature and re-loading
    creates the new feature on the target."""
    # Given - initial load
    data = full_export(organisation.id)
    _dump_and_load(data)

    initial_feature_count = Feature.objects.filter(
        project__organisation=organisation
    ).count()

    # When - create a new feature and re-export/load
    new_feature = Feature.objects.create(
        project=project, name="new_feature", initial_value="hello"
    )

    updated_data = full_export(organisation.id)
    _dump_and_load(updated_data)

    # Then - the new feature exists
    assert Feature.objects.filter(uuid=new_feature.uuid).exists()
    assert (
        Feature.objects.filter(project__organisation=organisation).count()
        == initial_feature_count + 1
    )

    # And its feature state value is correct
    new_fs = FeatureState.objects.get(
        feature=new_feature,
        environment=environment,
        identity=None,
        feature_segment=None,
    )
    assert new_fs.feature_state_value.string_value == "hello"


def test_full_export_loaddata__incremental_new_segment_override(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
    segment: Segment,
):
    """After an initial load, adding a segment override and re-loading
    creates the override on the target."""
    # Given - initial load
    data = full_export(organisation.id)
    _dump_and_load(data)

    # When - create a segment override
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    segment_fs = FeatureState.objects.create(
        feature=feature,
        feature_segment=feature_segment,
        environment=environment,
    )
    segment_fs.feature_state_value.string_value = "segment_override_value"
    segment_fs.feature_state_value.save()

    updated_data = full_export(organisation.id)
    _dump_and_load(updated_data)

    # Then - the segment override exists
    loaded_segment_fs = FeatureState.objects.get(uuid=segment_fs.uuid)
    assert loaded_segment_fs.feature_segment is not None
    assert (
        loaded_segment_fs.feature_state_value.string_value == "segment_override_value"
    )


def test_full_export_loaddata__incremental_toggle_feature_enabled(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    """Toggling a feature's enabled state and re-loading propagates
    the change."""
    # Given - initial state
    fs = FeatureState.objects.get(
        feature=feature, environment=environment, identity=None, feature_segment=None
    )
    assert fs.enabled is False

    data = full_export(organisation.id)
    _dump_and_load(data)

    # When - toggle feature enabled and re-export/load
    fs.enabled = True
    fs.save()

    updated_data = full_export(organisation.id)
    _dump_and_load(updated_data)

    # Then
    fs.refresh_from_db()
    assert fs.enabled is True


def test_full_export_loaddata__multivariate_feature(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    """Multivariate features with options and percentage allocations
    survive a full export/loaddata roundtrip."""
    # Given
    mv_feature = Feature.objects.create(
        project=project, name="mv_feature", type=MULTIVARIATE
    )
    option_a = MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=30,
        type=STRING,
        string_value="option_a",
    )
    option_b = MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=70,
        type=STRING,
        string_value="option_b",
    )

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert MultivariateFeatureOption.objects.filter(uuid=option_a.uuid).exists()
    assert MultivariateFeatureOption.objects.filter(uuid=option_b.uuid).exists()

    loaded_option_a = MultivariateFeatureOption.objects.get(uuid=option_a.uuid)
    assert loaded_option_a.string_value == "option_a"
    assert loaded_option_a.default_percentage_allocation == 30

    loaded_option_b = MultivariateFeatureOption.objects.get(uuid=option_b.uuid)
    assert loaded_option_b.string_value == "option_b"
    assert loaded_option_b.default_percentage_allocation == 70

    # Verify multivariate feature state values exist
    mv_fs = FeatureState.objects.get(
        feature=mv_feature,
        environment=environment,
        identity=None,
        feature_segment=None,
    )
    mv_fs_values = MultivariateFeatureStateValue.objects.filter(feature_state=mv_fs)
    assert mv_fs_values.count() == 2


def test_full_export_loaddata__segments_with_rules_and_conditions(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
):
    """Segments with nested rules and conditions survive a roundtrip."""
    # Given
    segment = Segment.objects.create(project=project, name="power_users")
    rule = SegmentRule.objects.create(segment=segment, type=ALL_RULE)
    Condition.objects.create(
        rule=rule, operator=EQUAL, property="subscription", value="premium"
    )

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert Segment.objects.filter(uuid=segment.uuid).exists()
    loaded_segment = Segment.objects.get(uuid=segment.uuid)
    assert loaded_segment.name == "power_users"

    loaded_rules = SegmentRule.objects.filter(segment=loaded_segment)
    assert loaded_rules.count() == 1

    loaded_conditions = Condition.objects.filter(rule=loaded_rules.first())
    assert loaded_conditions.count() == 1
    loaded_condition = loaded_conditions.first()
    assert loaded_condition is not None
    assert loaded_condition.property == "subscription"
    assert loaded_condition.value == "premium"


def test_full_export_loaddata__identity_overrides(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
    feature: Feature,
):
    """Identity-specific feature state overrides survive a roundtrip."""
    # Given
    identity = Identity.objects.create(
        identifier="override_user", environment=environment
    )
    identity_fs = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity
    )
    identity_fs.enabled = True
    identity_fs.save()
    identity_fs.feature_state_value.string_value = "user_specific_value"
    identity_fs.feature_state_value.save()

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    loaded_fs = FeatureState.objects.get(uuid=identity_fs.uuid)
    assert loaded_fs.identity is not None
    assert loaded_fs.identity.identifier == "override_user"
    assert loaded_fs.enabled is True
    assert loaded_fs.feature_state_value.string_value == "user_specific_value"


def test_full_export_loaddata__integrations(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    """Project-level and environment-level integrations survive a roundtrip."""
    # Given
    dd_config = DataDogConfiguration.objects.create(
        project=project, api_key="dd-api-key"
    )
    heap_config = HeapConfiguration.objects.create(
        environment=environment, api_key="heap-api-key"
    )

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert DataDogConfiguration.objects.filter(uuid=dd_config.uuid).exists()
    loaded_dd = DataDogConfiguration.objects.get(uuid=dd_config.uuid)
    assert loaded_dd.api_key == "dd-api-key"

    assert HeapConfiguration.objects.filter(uuid=heap_config.uuid).exists()
    loaded_heap = HeapConfiguration.objects.get(uuid=heap_config.uuid)
    assert loaded_heap.api_key == "heap-api-key"


def test_full_export_loaddata__subscription(  # type: ignore[no-untyped-def]
    organisation: Organisation,
):
    """Organisation subscription data survives a roundtrip."""
    # Given
    subscription = Subscription.objects.get(organisation=organisation)
    subscription_uuid = subscription.uuid

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    assert Subscription.objects.filter(uuid=subscription_uuid).exists()


def test_full_export_loaddata__multiple_environments(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
):
    """Multiple environments with separate feature states are correctly
    handled."""
    # Given
    env_dev = Environment.objects.create(project=project, name="Development")
    env_prod = Environment.objects.create(project=project, name="Production")

    feature = Feature.objects.create(
        project=project, name="multi_env_feature", initial_value="default"
    )

    # Set different values per environment
    fs_dev = FeatureState.objects.get(
        feature=feature, environment=env_dev, identity=None, feature_segment=None
    )
    fs_dev.feature_state_value.string_value = "dev_value"
    fs_dev.feature_state_value.save()

    fs_prod = FeatureState.objects.get(
        feature=feature, environment=env_prod, identity=None, feature_segment=None
    )
    fs_prod.feature_state_value.string_value = "prod_value"
    fs_prod.feature_state_value.save()

    # When
    data = full_export(organisation.id)
    _dump_and_load(data)

    # Then
    loaded_fs_dev = FeatureState.objects.get(uuid=fs_dev.uuid)
    assert loaded_fs_dev.feature_state_value.string_value == "dev_value"

    loaded_fs_prod = FeatureState.objects.get(uuid=fs_prod.uuid)
    assert loaded_fs_prod.feature_state_value.string_value == "prod_value"


def test_full_export_loaddata__dynamo_project_exported_with_dynamo_disabled(  # type: ignore[no-untyped-def]
    organisation: Organisation,
):
    """Projects with enable_dynamo_db=True are exported with
    enable_dynamo_db=False, and loaddata reflects that."""
    # Given
    dynamo_project = Project.objects.create(
        organisation=organisation,
        name="Dynamo Project",
        enable_dynamo_db=True,
    )

    # When
    data = full_export(organisation.id)

    # Verify export has dynamo disabled
    project_entries = [entry for entry in data if entry["model"] == "projects.project"]
    for entry in project_entries:
        assert entry["fields"]["enable_dynamo_db"] is False

    _dump_and_load(data)

    # Then
    loaded_project = Project.objects.get(uuid=dynamo_project.uuid)
    assert loaded_project.enable_dynamo_db is False


def test_full_export_loaddata__only_live_segments_exported(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
):
    """Only live segments (not draft versions) are included in the
    export and loaded."""
    # Given
    live_segment = Segment.objects.create(project=project, name="live_segment")
    SegmentRule.objects.create(segment=live_segment, type=ALL_RULE)

    # Create a draft version of the segment
    draft_segment = Segment.objects.create(
        project=project, name="draft_version", version_of=live_segment
    )

    # When
    data = full_export(organisation.id)

    # Then - only the live segment should be in the export
    segment_entries = [entry for entry in data if entry["model"] == "segments.segment"]
    segment_uuids = {entry["fields"]["uuid"] for entry in segment_entries}
    assert str(live_segment.uuid) in segment_uuids
    assert str(draft_segment.uuid) not in segment_uuids


# ================================================================
# Known limitation tests: document issues found during the spike
# ================================================================


def test_full_export_loaddata__trait_reload_fails__no_get_by_natural_key(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    """KNOWN LIMITATION: Trait model lacks get_by_natural_key on its
    manager. When loaddata encounters an existing trait, it attempts
    an INSERT (instead of UPDATE) and fails with IntegrityError.

    This means incremental updates to organisations that include
    identities with traits will fail unless the traits are deleted
    from the target first."""
    # Given - an identity with a trait
    identity = Identity.objects.create(identifier="trait_user", environment=environment)
    Trait.objects.create(identity=identity, trait_key="plan", string_value="enterprise")

    # When - export and reload into the same DB
    data = full_export(organisation.id)

    # Then - loaddata fails with IntegrityError on the trait
    with pytest.raises(IntegrityError, match="environments_trait"):
        _dump_and_load(data)


def test_full_export_loaddata__environment_api_key_reload_fails__no_get_by_natural_key(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    """KNOWN LIMITATION: EnvironmentAPIKey model lacks
    get_by_natural_key on its manager. When loaddata encounters an
    existing API key, it attempts an INSERT and fails with
    IntegrityError.

    This means incremental updates to organisations that include
    server-side API keys will fail unless the keys are deleted
    from the target first."""
    # Given - an environment with a server-side API key
    EnvironmentAPIKey.objects.create(environment=environment)

    # When - export and reload into the same DB
    data = full_export(organisation.id)

    # Then - loaddata fails with IntegrityError on the API key
    with pytest.raises(IntegrityError, match="environmentapikey"):
        _dump_and_load(data)


def test_full_export_loaddata__v2_versioning_fails__uuid_natural_key_conflict(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    """KNOWN LIMITATION: v2 feature versioning export produces data
    that loaddata cannot deserialise. The EnvironmentFeatureVersion
    UUID natural key is serialised as a list (e.g. ['uuid-string'])
    rather than a plain UUID string, causing a ValidationError during
    deserialisation."""
    # Given - v2 versioning enabled
    environment.use_v2_feature_versioning = True
    environment.save()

    Feature.objects.create(project=project, name="v2_feature")

    # When - export
    data = full_export(organisation.id)

    # Then - loaddata fails with DeserializationError
    with pytest.raises(DeserializationError):
        _dump_and_load(data)


def test_full_export_loaddata__deletion_not_propagated(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    environment: Environment,
):
    """KNOWN LIMITATION: loaddata does NOT remove objects absent from
    the dump. A feature deleted on the source will still exist on the
    target after re-loading. Deletions must be handled separately.

    To simulate this on a single database: first export with only
    feature_a, then verify that loading this export does not remove
    feature_b which was created separately on the 'target'."""
    # Given - on the "source", only feature_a exists
    feature_a = Feature.objects.create(
        project=project, name="feature_a", initial_value="a"
    )
    source_data = full_export(organisation.id)

    # Simulate "target" having an extra feature_b that the source doesn't
    feature_b = Feature.objects.create(
        project=project, name="feature_b", initial_value="b"
    )
    feature_b_uuid = feature_b.uuid

    # When - load the source data (which lacks feature_b) into the target
    _dump_and_load(source_data)

    # Then - feature_b still exists (loaddata never deletes)
    assert Feature.objects.filter(uuid=feature_b_uuid).exists()
    assert Feature.objects.filter(uuid=feature_a.uuid).exists()
