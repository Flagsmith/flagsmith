from typing import Any

from django_test_migrations.migrator import Migrator


def _condition(prerequisite_name: str) -> dict[str, Any]:
    return {
        "property": f'$.flags["{prerequisite_name}"].enabled',
        "operator": "NOT_EQUAL",
        "value": "true",
        "description": None,
    }


def test_0002__segment_with_several_prerequisites__splits_into_segment_per_prerequisite(
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
    checkout = Feature.objects.create(name="checkout", project=project)
    payments = Feature.objects.create(name="payments", project=project)
    inventory = Feature.objects.create(name="inventory", project=project)
    variant = MultivariateFeatureOption.objects.create(
        feature=checkout, key="fast", type="unicode", string_value="fast"
    )
    user_segment = Segment.objects.create(name="beta", project=project)
    old_segments = []
    for environment in environments:
        old_segment = Segment.objects.create(
            name=f"checkout-dependencies-{environment.api_key}",
            project=project,
            feature=checkout,
            is_system_segment=True,
            rules_data=[
                {
                    "type": "ANY",
                    "conditions": [_condition("payments"), _condition("inventory")],
                    "rules": [],
                }
            ],
        )
        for index, prerequisite in enumerate((payments, inventory)):
            SegmentFlagReference.objects.create(
                segment=old_segment,
                prerequisite_feature=prerequisite,
                condition_json_path=f"$[0].conditions[{index}]",
            )
        for segment, priority, enabled in (
            (old_segment, 0, False),
            (user_segment, 1, True),
        ):
            feature_segment = FeatureSegment.objects.create(
                feature=checkout,
                environment=environment,
                segment=segment,
                priority=priority,
            )
            feature_state = FeatureState.objects.create(
                feature=checkout,
                environment=environment,
                feature_segment=feature_segment,
                enabled=enabled,
            )
            FeatureStateValue.objects.create(
                feature_state=feature_state, type="unicode", string_value="old"
            )
            MultivariateFeatureStateValue.objects.create(
                feature_state=feature_state,
                multivariate_feature_option=variant,
                percentage_allocation=30,
            )
        old_segments.append(old_segment)

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_dependencies", "0002_split_dependency_segments")
    )

    # Then
    apps = new_state.apps
    FeatureSegment = apps.get_model("features", "FeatureSegment")
    Segment = apps.get_model("segments", "Segment")
    SegmentFlagReference = apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )
    new_segments = list(
        Segment.objects.filter(is_system_segment=True, deleted_at__isnull=True)
        .order_by("id")
        .values("name", "feature_id", "rules_data")
    )
    assert new_segments == [
        {
            "name": f"checkout-depends-on-{prerequisite_name}",
            "feature_id": checkout.id,
            "rules_data": [
                {
                    "type": "ANY",
                    "conditions": [_condition(prerequisite_name)],
                    "rules": [],
                }
            ],
        }
        for prerequisite_name in ("payments", "inventory")
    ]
    assert not Segment.objects.filter(
        id__in=[segment.id for segment in old_segments], deleted_at__isnull=True
    ).exists()
    assert list(
        SegmentFlagReference.objects.order_by("prerequisite_feature_id").values_list(
            "segment__name", "prerequisite_feature_id", "condition_json_path"
        )
    ) == [
        ("checkout-depends-on-payments", payments.id, "$[0].conditions[0]"),
        ("checkout-depends-on-inventory", inventory.id, "$[0].conditions[0]"),
    ]
    for environment in environments:
        assert list(
            FeatureSegment.objects.filter(environment_id=environment.id)
            .order_by("priority")
            .values_list(
                "segment__name",
                "priority",
                "feature_states__enabled",
                "feature_states__feature_state_value__string_value",
                "feature_states__multivariate_feature_state_values__percentage_allocation",
            )
        ) == [
            ("checkout-depends-on-payments", 0, False, "old", 30),
            ("checkout-depends-on-inventory", 1, False, "old", 30),
            ("beta", 2, True, "old", 30),
        ]


def test_0002__segment_is_not_a_dependency_segment__leaves_it_alone(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_dependencies", "0001_initial")
    )
    apps = old_state.apps
    Feature = apps.get_model("features", "Feature")
    Organisation = apps.get_model("organisations", "Organisation")
    Project = apps.get_model("projects", "Project")
    Segment = apps.get_model("segments", "Segment")
    SegmentFlagReference = apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    checkout = Feature.objects.create(name="checkout", project=project)
    payments = Feature.objects.create(name="payments", project=project)
    rules_data = [
        {
            "type": "ANY",
            "conditions": [_condition("payments")],
            "rules": [],
        }
    ]
    segment = Segment.objects.create(
        name="checkout-rollout",
        project=project,
        feature=checkout,
        is_system_segment=True,
        rules_data=rules_data,
    )
    SegmentFlagReference.objects.create(
        segment=segment,
        prerequisite_feature=payments,
        condition_json_path="$[0].conditions[0]",
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_dependencies", "0002_split_dependency_segments")
    )

    # Then
    Segment = new_state.apps.get_model("segments", "Segment")
    assert list(
        Segment.objects.filter(is_system_segment=True).values_list(
            "name", "deleted_at", "rules_data"
        )
    ) == [("checkout-rollout", None, rules_data)]


def _create_old_dependency_segment(
    apps: Any,
    *,
    environment: Any,
    feature: Any,
    prerequisites: list[Any],
    referenced_prerequisites: list[Any] | None = None,
) -> Any:
    FeatureSegment = apps.get_model("features", "FeatureSegment")
    FeatureState = apps.get_model("features", "FeatureState")
    Segment = apps.get_model("segments", "Segment")
    SegmentFlagReference = apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )
    segment = Segment.objects.create(
        name=f"{feature.name}-dependencies-{environment.api_key}",
        project=feature.project,
        feature=feature,
        is_system_segment=True,
        rules_data=[
            {
                "type": "ANY",
                "conditions": [
                    _condition(prerequisite.name) for prerequisite in prerequisites
                ],
                "rules": [],
            }
        ],
    )
    for index, prerequisite in enumerate(prerequisites):
        if referenced_prerequisites is None or prerequisite in referenced_prerequisites:
            SegmentFlagReference.objects.create(
                segment=segment,
                prerequisite_feature=prerequisite,
                condition_json_path=f"$[0].conditions[{index}]",
            )
    feature_segment = FeatureSegment.objects.create(
        feature=feature, environment=environment, segment=segment, priority=0
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=False,
    )
    return segment


def test_0002__segments_with_single_prerequisite__share_one_segment(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_dependencies", "0001_initial")
    )
    apps = old_state.apps
    Environment = apps.get_model("environments", "Environment")
    Feature = apps.get_model("features", "Feature")
    Organisation = apps.get_model("organisations", "Organisation")
    Project = apps.get_model("projects", "Project")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    checkout = Feature.objects.create(name="checkout", project=project)
    payments = Feature.objects.create(name="payments", project=project)
    for name in ("production", "staging"):
        _create_old_dependency_segment(
            apps,
            environment=Environment.objects.create(
                name=name, project=project, api_key=name
            ),
            feature=checkout,
            prerequisites=[payments],
        )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_dependencies", "0002_split_dependency_segments")
    )

    # Then
    apps = new_state.apps
    FeatureSegment = apps.get_model("features", "FeatureSegment")
    Segment = apps.get_model("segments", "Segment")
    (segment,) = Segment.objects.filter(is_system_segment=True, deleted_at__isnull=True)
    assert segment.name == "checkout-depends-on-payments"
    assert segment.flag_references.count() == 1
    assert list(
        FeatureSegment.objects.order_by("environment__name").values_list(
            "environment__name", "segment_id", "priority"
        )
    ) == [("production", segment.id, 0), ("staging", segment.id, 0)]


def test_0002__prerequisite_hard_deleted__drops_its_condition(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_dependencies", "0001_initial")
    )
    apps = old_state.apps
    Environment = apps.get_model("environments", "Environment")
    Feature = apps.get_model("features", "Feature")
    Organisation = apps.get_model("organisations", "Organisation")
    Project = apps.get_model("projects", "Project")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    environment = Environment.objects.create(
        name="production", project=project, api_key="production"
    )
    checkout = Feature.objects.create(name="checkout", project=project)
    payments = Feature.objects.create(name="payments", project=project)
    inventory = Feature.objects.create(name="inventory", project=project)
    _create_old_dependency_segment(
        apps,
        environment=environment,
        feature=checkout,
        prerequisites=[payments, inventory],
        referenced_prerequisites=[inventory],
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_dependencies", "0002_split_dependency_segments")
    )

    # Then
    FeatureSegment = new_state.apps.get_model("features", "FeatureSegment")
    assert list(
        FeatureSegment.objects.values_list("segment__name", "segment__rules_data")
    ) == [
        (
            "checkout-depends-on-inventory",
            [{"type": "ANY", "conditions": [_condition("inventory")], "rules": []}],
        )
    ]
