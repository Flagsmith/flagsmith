from typing import Any

from django_test_migrations.migrator import Migrator


def _condition(prerequisite_name: str) -> dict[str, Any]:
    return {
        "property": f'$.flags["{prerequisite_name}"].enabled',
        "operator": "NOT_EQUAL",
        "value": "true",
        "description": None,
    }


def _rules(*prerequisite_names: str) -> list[dict[str, Any]]:
    return [
        {
            "type": "ANY",
            "conditions": [_condition(name) for name in prerequisite_names],
            "rules": [],
        }
    ]


def test_0002__dependency_segments__splits_into_segment_per_prerequisite(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_dependencies", "0001_initial")
    )
    apps = old_state.apps
    Environment = apps.get_model("environments", "Environment")
    Feature = apps.get_model("features", "Feature")
    FeatureSegment = apps.get_model("features", "FeatureSegment")
    FeatureState = apps.get_model("features", "FeatureState")
    FeatureStateValue = apps.get_model("features", "FeatureStateValue")
    MultivariateFeatureOption = apps.get_model(
        "multivariate", "MultivariateFeatureOption"
    )
    MultivariateFeatureStateValue = apps.get_model(
        "multivariate", "MultivariateFeatureStateValue"
    )
    Organisation = apps.get_model("organisations", "Organisation")
    Project = apps.get_model("projects", "Project")
    Segment = apps.get_model("segments", "Segment")
    SegmentFlagReference = apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    environments = [
        Environment.objects.create(name=name, project=project, api_key=name)
        for name in ("production", "staging")
    ]
    features = {
        name: Feature.objects.create(name=name, project=project)
        for name in (
            "checkout",
            "storefront",
            "basket",
            "wishlist",
            "payments",
            "inventory",
        )
    }
    variant = MultivariateFeatureOption.objects.create(
        feature=features["checkout"], key="fast", type="unicode", string_value="fast"
    )
    user_segment = Segment.objects.create(name="beta", project=project)

    def create_override(
        environment: Any, feature: Any, segment: Any, priority: int, enabled: bool
    ) -> None:
        feature_state = FeatureState.objects.create(
            feature=feature,
            environment=environment,
            feature_segment=FeatureSegment.objects.create(
                feature=feature,
                environment=environment,
                segment=segment,
                priority=priority,
            ),
            enabled=enabled,
        )
        FeatureStateValue.objects.create(
            feature_state=feature_state, type="unicode", string_value="old"
        )
        if feature == features["checkout"]:
            MultivariateFeatureStateValue.objects.create(
                feature_state=feature_state,
                multivariate_feature_option=variant,
                percentage_allocation=30,
            )

    def create_old_segment(
        environment: Any,
        feature_name: str,
        prerequisite_names: list[str],
        referenced_names: list[str],
    ) -> Any:
        segment = Segment.objects.create(
            name=f"{feature_name}-dependencies-{environment.api_key}",
            project=project,
            feature=features[feature_name],
            is_system_segment=True,
            rules_data=_rules(*prerequisite_names),
        )
        for index, name in enumerate(prerequisite_names):
            if name in referenced_names:
                SegmentFlagReference.objects.create(
                    segment=segment,
                    prerequisite_feature=features[name],
                    condition_json_path=f"$[0].conditions[{index}]",
                )
        create_override(environment, features[feature_name], segment, 0, False)
        return segment

    old_segments = []
    for environment in environments:
        # Several prerequisites, followed by a user segment override.
        old_segments.append(
            create_old_segment(
                environment,
                "checkout",
                ["payments", "inventory"],
                ["payments", "inventory"],
            )
        )
        create_override(environment, features["checkout"], user_segment, 1, True)
        # A single prerequisite, whose rules already match the new form.
        old_segments.append(
            create_old_segment(environment, "storefront", ["payments"], ["payments"])
        )
    # A hard-deleted prerequisite, whose reference is gone.
    old_segments.append(
        create_old_segment(
            environments[0], "basket", ["payments", "inventory"], ["inventory"]
        )
    )
    # A reference that no longer matches the rules.
    create_old_segment(
        environments[0], "wishlist", ["payments"], ["payments"]
    ).flag_references.update(condition_json_path="$[0].conditions[5]")
    # Another system segment referencing a flag, not created for a dependency.
    Segment.objects.create(
        name="checkout-rollout",
        project=project,
        feature=features["checkout"],
        is_system_segment=True,
        rules_data=_rules("payments"),
    ).flag_references.create(
        prerequisite_feature=features["payments"],
        condition_json_path="$[0].conditions[0]",
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_dependencies", "0002_split_dependency_segments")
    )

    # Then
    apps = new_state.apps
    FeatureSegment = apps.get_model("features", "FeatureSegment")
    Segment = apps.get_model("segments", "Segment")
    assert list(
        Segment.objects.filter(is_system_segment=True, deleted_at__isnull=True)
        .order_by("name")
        .values_list("name", "feature__name", "rules_data")
    ) == [
        ("basket-depends-on-inventory", "basket", _rules("inventory")),
        ("checkout-depends-on-inventory", "checkout", _rules("inventory")),
        ("checkout-depends-on-payments", "checkout", _rules("payments")),
        ("checkout-rollout", "checkout", _rules("payments")),
        ("storefront-depends-on-payments", "storefront", _rules("payments")),
        ("wishlist-dependencies-production", "wishlist", _rules("payments")),
    ]
    assert not Segment.objects.filter(
        id__in=[segment.id for segment in old_segments], deleted_at__isnull=True
    ).exists()
    assert list(
        Segment.objects.filter(deleted_at__isnull=True, flag_references__isnull=False)
        .order_by("name")
        .values_list(
            "name",
            "flag_references__prerequisite_feature__name",
            "flag_references__condition_json_path",
        )
    ) == [
        ("basket-depends-on-inventory", "inventory", "$[0].conditions[0]"),
        ("checkout-depends-on-inventory", "inventory", "$[0].conditions[0]"),
        ("checkout-depends-on-payments", "payments", "$[0].conditions[0]"),
        ("checkout-rollout", "payments", "$[0].conditions[0]"),
        ("storefront-depends-on-payments", "payments", "$[0].conditions[0]"),
        ("wishlist-dependencies-production", "payments", "$[0].conditions[5]"),
    ]
    assert list(
        FeatureSegment.objects.order_by("environment__name", "feature__name", "priority")
        .values_list(
            "environment__name",
            "feature__name",
            "segment__name",
            "priority",
            "feature_states__enabled",
            "feature_states__feature_state_value__string_value",
            "feature_states__multivariate_feature_state_values__percentage_allocation",
        )
    ) == [
        ("production", "basket", "basket-depends-on-inventory", 0, False, "old", None),
        ("production", "checkout", "checkout-depends-on-payments", 0, False, "old", 30),
        ("production", "checkout", "checkout-depends-on-inventory", 1, False, "old", 30),
        ("production", "checkout", "beta", 2, True, "old", 30),
        ("production", "storefront", "storefront-depends-on-payments", 0, False, "old", None),
        ("production", "wishlist", "wishlist-dependencies-production", 0, False, "old", None),
        ("staging", "checkout", "checkout-depends-on-payments", 0, False, "old", 30),
        ("staging", "checkout", "checkout-depends-on-inventory", 1, False, "old", 30),
        ("staging", "checkout", "beta", 2, True, "old", 30),
        ("staging", "storefront", "storefront-depends-on-payments", 0, False, "old", None),
    ]  # fmt: skip
