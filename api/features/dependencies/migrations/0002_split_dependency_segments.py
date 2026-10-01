import uuid
from typing import Any

import jsonpath_rfc9535
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.utils import timezone


def _clone(instance: Any, **attrs: Any) -> Any:
    instance.pk = None
    instance.id = None
    instance.uuid = uuid.uuid4()
    for name, value in attrs.items():
        setattr(instance, name, value)
    instance.save()
    return instance


def split_dependency_segments(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    """Replace each `{feature}-dependencies-{environment}` segment, holding all
    of a feature's prerequisites, by one immutable segment per prerequisite.

    Every override on the old segment, including those in past versions, is
    replaced in place by one override per prerequisite, so evaluation results
    don't change. No new versions are published.
    """
    Condition = apps.get_model("segments", "Condition")
    FeatureSegment = apps.get_model("features", "FeatureSegment")
    FeatureState = apps.get_model("features", "FeatureState")
    FeatureStateValue = apps.get_model("features", "FeatureStateValue")
    MultivariateFeatureStateValue = apps.get_model(
        "multivariate", "MultivariateFeatureStateValue"
    )
    Segment = apps.get_model("segments", "Segment")
    SegmentFlagReference = apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )
    SegmentRule = apps.get_model("segments", "SegmentRule")

    # Segments created so far, by dependent and prerequisite feature IDs. Only
    # this migration creates segments of the new form, so no lookup is needed.
    dependency_segments: dict[tuple[int, int], Any] = {}

    def get_or_create_dependency_segment(
        old_segment: Any, prerequisite_feature_id: int, condition: Any
    ) -> Any:
        key = (old_segment.feature_id, prerequisite_feature_id)
        if segment := dependency_segments.get(key):
            return segment
        rules = [{"type": "ANY", "conditions": [condition], "rules": []}]
        prerequisite_feature_name = (
            SegmentFlagReference.objects.filter(
                segment=old_segment,
                prerequisite_feature_id=prerequisite_feature_id,
            )
            .values_list("prerequisite_feature__name", flat=True)
            .first()
        )
        segment = Segment.objects.create(
            project_id=old_segment.project_id,
            name=f"{old_segment.feature.name}-depends-on-{prerequisite_feature_name}",
            is_system_segment=True,
            feature_id=old_segment.feature_id,
            rules_data=rules,
            version=1,
        )
        Segment.objects.filter(pk=segment.pk).update(version_of=segment)
        rule = SegmentRule.objects.create(segment=segment, type="ANY")
        Condition.objects.create(
            rule=rule,
            operator=condition["operator"],
            property=condition["property"],
            value=condition["value"],
            description=condition["description"],
        )
        SegmentFlagReference.objects.create(
            segment=segment,
            prerequisite_feature_id=prerequisite_feature_id,
            condition_json_path="$[0].conditions[0]",
        )
        dependency_segments[key] = segment
        return segment

    old_segments = list(
        Segment.objects.filter(
            is_system_segment=True,
            deleted_at__isnull=True,
            feature__isnull=False,
            flag_references__isnull=False,
        )
        .select_related("feature")
        .distinct()
    )
    for old_segment in old_segments:
        if not old_segment.name.startswith(f"{old_segment.feature.name}-dependencies-"):
            continue
        # A hard-deleted prerequisite leaves its condition behind without a
        # reference. Its flag is absent from evaluation, so the condition never
        # matches, and dropping it doesn't change evaluation results. References
        # are indexed in the order of their conditions, preserving priorities.
        new_segments = [
            get_or_create_dependency_segment(
                old_segment,
                prerequisite_feature_id,
                jsonpath_rfc9535.find(json_path, old_segment.rules_data).values()[0],
            )
            for json_path, prerequisite_feature_id in SegmentFlagReference.objects.filter(
                segment=old_segment
            )
            .order_by("id")
            .values_list("condition_json_path", "prerequisite_feature_id")
        ]
        for override in FeatureSegment.objects.filter(segment=old_segment):
            # Make room for the extra overrides right after the replaced one.
            FeatureSegment.objects.filter(
                feature_id=override.feature_id,
                environment_id=override.environment_id,
                environment_feature_version_id=override.environment_feature_version_id,
                priority__gt=override.priority,
            ).update(priority=models.F("priority") + len(new_segments) - 1)
            feature_states = list(
                FeatureState.objects.filter(
                    feature_segment=override, deleted_at__isnull=True
                )
            )
            for offset, new_segment in enumerate(new_segments[1:], start=1):
                new_override = _clone(
                    FeatureSegment.objects.get(pk=override.pk),
                    segment=new_segment,
                    priority=override.priority + offset,
                )
                for feature_state in feature_states:
                    feature_state_id = feature_state.pk
                    new_feature_state = _clone(
                        FeatureState.objects.get(pk=feature_state_id),
                        feature_segment=new_override,
                    )
                    for value in FeatureStateValue.objects.filter(
                        feature_state_id=feature_state_id
                    ):
                        _clone(value, feature_state=new_feature_state)
                    for value in MultivariateFeatureStateValue.objects.filter(
                        feature_state_id=feature_state_id
                    ):
                        _clone(value, feature_state=new_feature_state)
            override.segment = new_segments[0]
            override.save(update_fields=["segment"])
        SegmentFlagReference.objects.filter(segment=old_segment).delete()
        Segment.objects.filter(pk=old_segment.pk).update(deleted_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [
        ("feature_dependencies", "0001_initial"),
        ("feature_versioning", "0008_add_last_modified_indexes"),
        ("multivariate", "0009_add_multivariate_feature_option_key"),
    ]

    operations = [
        migrations.RunPython(
            split_dependency_segments, reverse_code=migrations.RunPython.noop
        ),
    ]
