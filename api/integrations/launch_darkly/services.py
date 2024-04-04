import logging
import re
from contextlib import contextmanager
from typing import Callable, Optional, Tuple

from django.core import signing
from django.utils import timezone
from flag_engine.segments import constants
from requests.exceptions import RequestException

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE, STANDARD, FeatureType
from features.models import (
    Feature,
    FeatureSegment,
    FeatureState,
    FeatureStateValue,
)
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.value_types import STRING
from integrations.launch_darkly import types as ld_types
from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.constants import (
    LAUNCH_DARKLY_IMPORTED_DEFAULT_TAG_LABEL,
    LAUNCH_DARKLY_IMPORTED_TAG_COLOR,
)
from integrations.launch_darkly.models import (
    LaunchDarklyImportRequest,
    LaunchDarklyImportStatus,
)
from integrations.launch_darkly.types import Clause
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule
from users.models import FFAdminUser

logger = logging.getLogger(__name__)


def _sign_ld_value(value: str, user_id: int) -> str:
    return signing.dumps(value, salt=f"ld_import_{user_id}")


def _unsign_ld_value(value: str, user_id: int) -> str:
    return signing.loads(
        value,
        salt=f"ld_import_{user_id}",
    )


def _log_error(
    import_request: LaunchDarklyImportRequest,
    error_message: str,
) -> None:
    import_request.status["error_messages"] += [error_message]


@contextmanager
def _complete_import_request(
    import_request: LaunchDarklyImportRequest,
) -> None:
    """
    Wrap code so the import request always ends up completed.

    If no exception raised, assume successful import.

    In case wrapped code needs to expose an error to the user, it should populate
    `import_request.status["error_messages"]` before raising an exception.
    """
    try:
        yield
    except Exception as exc:
        import_request.status["result"] = "failure"
        raise exc
    else:
        import_request.status["result"] = "success"
    finally:
        import_request.ld_token = ""
        import_request.completed_at = timezone.now()
        import_request.save()


def _create_environments_from_ld(
    ld_environments: list[ld_types.Environment],
    project_id: int,
) -> dict[str, Environment]:
    environments_by_ld_environment_key: dict[str, Environment] = {}

    for ld_environment in ld_environments:
        (
            environments_by_ld_environment_key[ld_environment["key"]],
            _,
        ) = Environment.objects.get_or_create(
            name=ld_environment["name"],
            project_id=project_id,
        )

    return environments_by_ld_environment_key


def _create_tags_from_ld(
    ld_tags: list[str],
    project_id: int,
) -> dict[str, Tag]:
    tags_by_ld_tag = {}

    for ld_tag in (*ld_tags, LAUNCH_DARKLY_IMPORTED_DEFAULT_TAG_LABEL):
        tags_by_ld_tag[ld_tag], _ = Tag.objects.update_or_create(
            label=ld_tag,
            project_id=project_id,
            defaults={
                "color": LAUNCH_DARKLY_IMPORTED_TAG_COLOR,
            },
        )

    return tags_by_ld_tag


def _ld_operator_to_flagsmith_operator(ld_operator: str) -> Optional[str]:
    """
    Convert a Launch Darkly operator to its closest Flagsmith equivalent. If not convertible, return None.

    Based on: https://docs.launchdarkly.com/sdk/concepts/flag-evaluation-rules#operators

    :param ld_operator: the operator of the targeting rule.
    :return: the closest Flagsmith equivalent of the given Launch Darkly operator.
    """
    return {
        "in": constants.IN,
        "endsWith": constants.REGEX,
        "startsWith": constants.REGEX,
        "matches": constants.REGEX,
        "contains": constants.CONTAINS,
        "lessThan": constants.LESS_THAN,
        "lessThanOrEqual": constants.LESS_THAN_INCLUSIVE,
        "greaterThan": constants.GREATER_THAN,
        "greaterThanOrEqual": constants.GREATER_THAN_INCLUSIVE,
        "before": constants.LESS_THAN,
        "after": constants.GREATER_THAN,
        "semVerEqual": constants.EQUAL,
        "semVerLessThan": constants.LESS_THAN,
        "semVerGreaterThan": constants.GREATER_THAN,
    }.get(ld_operator, None)


def _convert_ld_values(values: list[str], ld_operator: str) -> list[str]:
    """
    Convert "values" of a Launch Darkly clause to Flagsmith compatible values. Some matching is converted to
    regex and some matching is consolidated into a single value. For example, if "in" operator is used, we join
    the values using the comma separator to make it Flagsmith-compliant.

    Note that a separate Clause should be created for each value in the lis and those clauses should be "OR"ed.
    This is how Launch Darkly handles multiple values for a single operator such as less than.

    :param values: the list of values from Launch Darkly's targeting rule.
    :param ld_operator: the operator of the targeting rule.
    :return: a list of values that is Flagsmith-compliant.
    """
    match ld_operator:
        case "in":
            # TODO: How to escape the comma itself?
            return list([",".join(values)])
        case "endsWith":
            return [".*" + re.escape(value) for value in values]
        case "startsWith":
            return [re.escape(value) + ".*" for value in values]
        case "semVerEqual" | "semVerLessThan" | "semVerGreaterThan":
            return [value + ":semver" for value in values]
        case _:
            return [value for value in values]


def _get_segment_name(name: str, env: str) -> str:
    """
    Generate a unique and descriptive name for the segment. This name is re-used on consecutive imports to
    prevent duplicate segments.

    :param name: Name of the Launch Darkly segment.
    :param env: Environment name of the Launch Darkly segment.
    :return: A unique and descriptive name for the segment targeting a specific environment.
    """
    return f"{name} (Override for {env})"


def _create_feature_segments_for_segment_match_clauses(
    import_request: LaunchDarklyImportRequest,
    clauses: list[Clause],
    project: Project,
    feature: Feature,
    environment: Environment,
    segments_by_ld_key: dict[str, Segment],
) -> list[FeatureSegment]:
    """
    Creates a feature segment if a rule contains "segmentMatch" operator. This shouldn't be used if clauses
    doesn't contain "segmentMatch" operator. Instead use "_create_feature_segment_from_clauses".

    This method can only accept clauses that contains "segmentMatch" operator. If there are other operators,
    we can't create corresponding Feature Segments. This is a technical limitation of how "FeatureSegment" is
    implemented in Flagsmith.

    :param clauses: a list of clauses from Launch Darkly's targeting rule.
    :param feature: the feature to target for the segment.
    :param segments_by_ld_key: a mapping from Launch Darkly segment key to Segment. Used to find right segment
    from the "segmentMatch" operator
    :return: a list of "FeatureSegment" operators created for each "segmentMatch" operator.
    """

    if any(clause["op"] != "segmentMatch" for clause in clauses):
        for clause in clauses:
            _log_error(
                import_request=import_request,
                error_message=f"Could not import segment clause {clause['attribute']} {clause['op']} for"
                f" {feature.name} in {environment.name}: nested segment match is not supported.",
            )
        return []

    if any(clause["negate"] is True for clause in clauses):
        _log_error(
            import_request=import_request,
            error_message=f"Negated segment match is not supported, skipping"
            f" for {feature.name} in {environment.name}",
        )
        return []

    # Complex rules that allow matching segments is not allowed in Flagsmith.
    # We can only emulate a single segment match by enabling the segment rule.
    all_targeted_segments: list[str] = sum([clause["values"] for clause in clauses], [])
    feature_states: list[FeatureState] = []
    for index, targeted_segment_key in enumerate(all_targeted_segments):
        if targeted_segment_key not in segments_by_ld_key:
            _log_error(
                import_request=import_request,
                error_message=f"Segment {targeted_segment_key} not found, skipping"
                f" for {feature.name} in {environment.name}",
            )
            continue
        targeted_segment_name = segments_by_ld_key[targeted_segment_key].name

        # We assume segment is already created.
        segment = Segment.objects.get(name=targeted_segment_name, project=project)

        feature_segment, _ = FeatureSegment.objects.update_or_create(
            feature=feature,
            segment=segment,
            environment=environment,
            priority=index,
        )

        # Enable rules by default. In LD, rules are enabled if the flag is on.
        feature_state, _ = FeatureState.objects.update_or_create(
            feature=feature,
            feature_segment=feature_segment,
            environment=environment,
            defaults={"enabled": True},
        )

        feature_states.append(feature_state)

    return feature_states


def _create_segment_rule_for_segment(
    import_request: LaunchDarklyImportRequest,
    segment: Segment,
    clauses: list[Clause],
) -> SegmentRule:
    """
    Create the SegmentRule for the given segment and clauses. This method doesn't handle any feature-specific
    segments. Use "_create_feature_segment_from_clauses" for that.

    :param segment: the segment to create the rule for.
    :param clauses: a list of clauses from Launch Darkly's segment rule. This describes which identities belong
    to the given segment.
    :return: the SegmentRule created for the given segment.
    """

    parent_rule, _ = SegmentRule.objects.get_or_create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    # TODO: Delete existing rules if parent_rule already exists.

    negated_child = None

    for clause in clauses:
        _property = clause["attribute"]
        operator = _ld_operator_to_flagsmith_operator(clause["op"])
        values = _convert_ld_values(
            [str(value) for value in clause["values"]], clause["op"]
        )

        if operator is not None:
            # Since there is no !X operation in Flagsmith, we wrap negated conditions in a none() rule.
            if clause["negate"] is True:
                # Create a negated child if it doesn't exist.
                if negated_child is None:
                    negated_child = SegmentRule.objects.create(
                        rule=parent_rule, type=SegmentRule.NONE_RULE
                    )

                target_rule = negated_child
            else:
                # Create a new child rule if it doesn't exist. Each child rule is "AND"ed together because
                # parent_rule has type of `ALL`. Also note that each Condition added to this child rule is
                # "OR"ed together. This is also how Launch Darkly works.
                child_rule = SegmentRule.objects.create(
                    rule=parent_rule, type=SegmentRule.ANY_RULE
                )
                target_rule = child_rule

            # Create a condition for each value. Each condition is "OR"ed together.
            for value in values:
                condition, _ = Condition.objects.update_or_create(
                    rule=target_rule,
                    property=_property,
                    value=value,
                    operator=operator,
                    created_with_segment=True,
                )
        else:
            _log_error(
                import_request=import_request,
                error_message=f"Can't map launch darkly operator: {clause['op']}"
                f" skipping for segment: {segment.name}",
            )

    return parent_rule


def _create_feature_segment_from_clauses(
    import_request: LaunchDarklyImportRequest,
    clauses: list[Clause],
    project: Project,
    feature: Feature,
    environment: Environment,
    segments_by_ld_key: dict[str, Segment],
    rule_name: str,
) -> list[FeatureState]:
    """
    Create one or multiple feature-specific segment for the given clauses. Note that "segmentMatch" operator
    is not fully supported. If "segmentMatch" is used, we create a feature rule for the given segment(s) instead
    of a feature-specific segment. Thus, we return multiple feature states if there are multiple segments being
    targeted.

    Also note that "segmentMatch" operator is not supported for nested rules. If a nested rule contains
    "segmentMatch", it can't use any other targeting operators. This is because we convert "segmentMatch" into
    a segment specific feature value, thus no further filter can be applied.

    :param clauses: a list of clauses from Launch Darkly's targeting rule.
    :param feature: the feature to target for identities.
    :param segments_by_ld_key: a mapping from Launch Darkly segment key to Segment. Used for "segmentMatch" op.
    :param rule_name: the name of the rule this feature-specific segment is created for.
    :return: a list of FeatureState objects for the newly created feature-specific segments.
    """
    # There is no "segmentMatch" operator in flagsmith, instead we create a targeting rule for that
    # specific segment.
    if "segmentMatch" in [clause["op"] for clause in clauses]:
        return _create_feature_segments_for_segment_match_clauses(
            import_request=import_request,
            clauses=clauses,
            project=project,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
        )

    # Create a feature specific segment for the rule.
    segment, _ = Segment.objects.update_or_create(
        name=rule_name, project=project, feature=feature
    )

    # Create a targeting rule for the new feature-specific segment.
    _create_segment_rule_for_segment(
        import_request=import_request,
        segment=segment,
        clauses=clauses,
    )

    # Tie the feature and segment together.
    feature_segment, _ = FeatureSegment.objects.update_or_create(
        feature=feature,
        segment=segment,
        environment=environment,
    )

    # Enable rules by default. In LD, rules are enabled if the flag is on.
    return [
        FeatureState.objects.update_or_create(
            feature=feature,
            feature_segment=feature_segment,
            environment=environment,
            defaults={"enabled": True},
        )[0]
    ]


def _import_targets(
    import_request: LaunchDarklyImportRequest,
    ld_flag_config: ld_types.FeatureFlagConfig,
    feature: Feature,
    environment: Environment,
    segments_by_ld_key: dict[str, Segment],
    mv_feature_options_by_variation: dict[str, MultivariateFeatureOption],
) -> None:
    """
    Import the individual targeting rules for the given Launch Darkly's feature flag.

    :param ld_flag_config: the feature flag config from Launch Darkly.
    :param feature: the feature to target for identities.
    :param environment: the environment to target for identities.
    :param mv_feature_options_by_variation: a mapping from variation index to MultivariateFeatureOption if the
    flag is multivariate.
    """
    if "targets" in ld_flag_config:
        # Identifiers are grouped by their variation index. So each target has the same variation index.
        for target in ld_flag_config["targets"]:
            # Create a segment override for those identities. This is a work-around to support individual
            # targeting in local evaluation mode.
            # TODO: Remove this when https://github.com/Flagsmith/flagsmith/issues/3132 is resolved.
            feature_states = _create_feature_segment_from_clauses(
                import_request=import_request,
                clauses=[
                    {
                        "attribute": "key",
                        "op": "in",
                        "values": target["values"],
                        "negate": False,
                    }
                ],
                project=feature.project,
                feature=feature,
                environment=environment,
                segments_by_ld_key=segments_by_ld_key,
                rule_name=f"individual-targeting-variation-{target['variation']}",
            )

            _set_imported_mv_feature_state_values(
                variation_idx=str(target["variation"]),
                rollout=None,
                feature_states=feature_states,
                mv_feature_options_by_variation=mv_feature_options_by_variation,
            )

            # Create individual identity targets.
            for identifier in target["values"]:
                identity, _ = Identity.objects.get_or_create(
                    identifier=identifier,
                    environment=environment,
                )
                identity.update_traits(
                    [
                        {
                            "trait_key": "key",
                            "trait_value": identifier,
                        }
                    ]
                )

                # Set identity overrides.
                if len(mv_feature_options_by_variation) == 0:
                    FeatureState.objects.update_or_create(
                        feature=feature,
                        feature_segment=None,
                        environment=environment,
                        identity=identity,
                        defaults={"enabled": target["variation"] == 0},
                    )
                else:
                    feature_state, _ = FeatureState.objects.update_or_create(
                        feature=feature,
                        feature_segment=None,
                        environment=environment,
                        identity=identity,
                        defaults={"enabled": True},
                    )

                    mv_feature_option = mv_feature_options_by_variation[
                        str(target["variation"])
                    ]
                    MultivariateFeatureStateValue.objects.update_or_create(
                        feature_state=feature_state,
                        multivariate_feature_option=mv_feature_option,
                        defaults={
                            "percentage_allocation": 100,
                        },
                    )

    if "contextTargets" in ld_flag_config and len(ld_flag_config["contextTargets"]) > 0:
        if (
            sum(
                [
                    len(context_target["values"])
                    for context_target in ld_flag_config["contextTargets"]
                ]
            )
            > 0
        ):
            _log_error(
                import_request=import_request,
                error_message=f"Context targets are not supported, skipping context targets for feature"
                f" {feature.name} in environment {environment.name}",
            )


def _set_imported_mv_feature_state_values(
    variation_idx: Optional[str],
    rollout: Optional[ld_types.Rollout],
    feature_states: list[FeatureState],
    mv_feature_options_by_variation: dict[str, MultivariateFeatureOption],
) -> None:
    """
    Set the feature states and multivariate feature states for recently imported flags.
    If none of 'variation_idx' and 'rollout' is set, nothing is done. If the flag is not multivariate,
    nothing is done.

    :param variation_idx: the variation index to set as the control value. This is the launch darkly variation
    index, not the index of the variation in Flagsmith.
    :param rollout: the rollout to set as the control value coming from Launch Darkly.
    :param feature_states: the feature states to set the values for.
    :param mv_feature_options_by_variation: a mapping from variation index to MultivariateFeatureOption if the
    flag is multivariate.
    """

    # For Multivariate flags, we need to set targeting rules for each variation.
    if len(mv_feature_options_by_variation) > 0:
        # For each feature state,
        for feature_state in feature_states:
            if variation_idx is not None:
                for mv_variation in mv_feature_options_by_variation:
                    mv_feature_option = mv_feature_options_by_variation[mv_variation]
                    # We expect only one variation to be set as the control.
                    # Control value is set to 100% and rest is set to 0%.
                    MultivariateFeatureStateValue.objects.update_or_create(
                        feature_state=feature_state,
                        multivariate_feature_option=mv_feature_option,
                        defaults={
                            "percentage_allocation": (
                                100 if variation_idx == mv_variation else 0
                            )
                        },
                    )
            elif rollout is not None:
                cumulative_rollout = rollout_baseline = 0
                for weighted_variation in rollout["variations"]:
                    # Find the corresponding variation value.
                    weight = weighted_variation["weight"]
                    cumulative_rollout += weight / 1000
                    cumulative_rollout_rounded = round(cumulative_rollout)

                    # LD has weights between 0-100,000. Flagsmith has weights between 0-100.
                    # While scaling down, we need to keep track of the cumulative rollout so the
                    # values will add up to 100%.
                    percentage_allocation = (
                        cumulative_rollout_rounded - rollout_baseline
                    )
                    rollout_baseline = cumulative_rollout_rounded

                    mv_feature_option = mv_feature_options_by_variation[
                        str(weighted_variation["variation"])
                    ]
                    MultivariateFeatureStateValue.objects.update_or_create(
                        feature_state=feature_state,
                        multivariate_feature_option=mv_feature_option,
                        defaults={"percentage_allocation": percentage_allocation},
                    )


def _import_rules(
    import_request: LaunchDarklyImportRequest,
    ld_flag_config: ld_types.FeatureFlagConfig,
    feature: Feature,
    environment: Environment,
    segments_by_ld_key: dict[str, Segment],
    mv_feature_options_by_variation: dict[str, MultivariateFeatureOption],
) -> None:
    """
    Import each rule in the given Launch Darkly's feature flag as a feature-specific segment in Flagsmith.

    :param ld_flag_config: the feature flag config from Launch Darkly.
    :param feature: the feature to import the rules to.
    :param segments_by_ld_key: a mapping from Launch Darkly segment key to Segment. Used for "segmentMatch" op.
    :param mv_feature_options_by_variation: a mapping from variation index to MultivariateFeatureOption if the
    flag is multivariate. Used for setting multivariate flag weights.
    """

    if "prerequisites" in ld_flag_config and len(ld_flag_config["prerequisites"]) > 0:
        _log_error(
            import_request=import_request,
            error_message=f"Prerequisites are not supported, skipping prerequisites for feature"
            f" {feature.name} in environment {environment.name}",
        )

    # For each rule in LD's flag,
    if "rules" in ld_flag_config:
        for rule in ld_flag_config["rules"]:
            # Generate a unique and descriptive name for the rule. This name is re-used on consecutive imports
            # to prevent duplicate rules.
            rule_name = rule.get("description", "imported-" + rule["_id"])
            # Create the feature segment for the given rule and get the feature state objects from those
            # newly created feature-specific segments.
            feature_states = _create_feature_segment_from_clauses(
                import_request=import_request,
                clauses=rule["clauses"],
                project=feature.project,
                feature=feature,
                environment=environment,
                segments_by_ld_key=segments_by_ld_key,
                rule_name=rule_name,
            )

            _set_imported_mv_feature_state_values(
                variation_idx=rule.get("variation", None),
                rollout=rule.get("rollout", None),
                feature_states=feature_states,
                mv_feature_options_by_variation=mv_feature_options_by_variation,
            )


def _create_boolean_feature_states_with_segments_identities(
    import_request: LaunchDarklyImportRequest,
    ld_flag: ld_types.FeatureFlag,
    feature: Feature,
    environments_by_ld_environment_key: dict[str, Environment],
    segments_by_ld_key: dict[str, Segment],
) -> None:
    for ld_environment_key, environment in environments_by_ld_environment_key.items():
        ld_flag_config = ld_flag["environments"][ld_environment_key]
        feature_state, _ = FeatureState.objects.update_or_create(
            feature=feature,
            feature_segment=None,
            environment=environment,
            defaults={"enabled": ld_flag_config["on"]},
        )

        FeatureStateValue.objects.update_or_create(
            feature_state=feature_state,
        )

        # TODO: Move target and rule creation to be invoked directly from `process_import_request`.
        # https://github.com/Flagsmith/flagsmith/issues/3383
        _import_targets(
            import_request=import_request,
            ld_flag_config=ld_flag_config,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
            mv_feature_options_by_variation={},
        )
        _import_rules(
            import_request=import_request,
            ld_flag_config=ld_flag_config,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
            mv_feature_options_by_variation={},
        )


def _create_string_feature_states_with_segments_identities(
    import_request: LaunchDarklyImportRequest,
    ld_flag: ld_types.FeatureFlag,
    feature: Feature,
    environments_by_ld_environment_key: dict[str, Environment],
    segments_by_ld_key: dict[str, Segment],
) -> None:
    variations_by_idx = {
        str(idx): variation for idx, variation in enumerate(ld_flag["variations"])
    }

    for ld_environment_key, environment in environments_by_ld_environment_key.items():
        ld_flag_config = ld_flag["environments"][ld_environment_key]

        is_flag_on = ld_flag_config["on"]
        if is_flag_on:
            variation_config_key = "isFallthrough"
        else:
            variation_config_key = "isOff"

        string_value = ""

        if ld_flag_config_summary := ld_flag_config.get("_summary"):
            enabled_variations = ld_flag_config_summary.get("variations") or {}
            for idx, variation_config in enabled_variations.items():
                if variation_config.get(variation_config_key):
                    string_value = variations_by_idx[idx]["value"]
                    break

        feature_state, _ = FeatureState.objects.update_or_create(
            feature=feature,
            feature_segment=None,
            environment=environment,
            defaults={"enabled": is_flag_on},
        )

        FeatureStateValue.objects.update_or_create(
            feature_state=feature_state,
            defaults={"type": STRING, "string_value": string_value},
        )

        # TODO: Move target and rule creation to be invoked directly from `process_import_request`.
        # https://github.com/Flagsmith/flagsmith/issues/3383
        _import_targets(
            import_request=import_request,
            ld_flag_config=ld_flag_config,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
            mv_feature_options_by_variation={},
        )
        _import_rules(
            import_request=import_request,
            ld_flag_config=ld_flag_config,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
            mv_feature_options_by_variation={},
        )


def _create_mv_feature_states_with_segments_identities(
    import_request: LaunchDarklyImportRequest,
    ld_flag: ld_types.FeatureFlag,
    feature: Feature,
    environments_by_ld_environment_key: dict[str, Environment],
    segments_by_ld_key: dict[str, Segment],
) -> None:
    variations = ld_flag["variations"]
    variation_values_by_idx: dict[str, str] = {}
    mv_feature_options_by_variation: dict[str, MultivariateFeatureOption] = {}

    for idx, variation in enumerate(variations):
        variation_idx = str(idx)
        variation_value = variation["value"]
        variation_values_by_idx[variation_idx] = variation_value
        (
            mv_feature_options_by_variation[str(idx)],
            _,
        ) = MultivariateFeatureOption.objects.update_or_create(
            feature=feature,
            string_value=variation_value,
            defaults={"default_percentage_allocation": 0, "type": STRING},
        )

    for ld_environment_key, environment in environments_by_ld_environment_key.items():
        ld_flag_config = ld_flag["environments"][ld_environment_key]

        is_flag_on = ld_flag_config["on"]

        feature_state, _ = FeatureState.objects.update_or_create(
            feature=feature,
            feature_segment=None,
            environment=environment,
            defaults={"enabled": is_flag_on},
        )

        cumulative_rollout = rollout_baseline = 0

        if ld_flag_config_summary := ld_flag_config.get("_summary"):
            enabled_variations = ld_flag_config_summary.get("variations") or {}
            for variation_idx, variation_config in enabled_variations.items():
                if variation_config.get("isOff"):
                    # Set LD's off value as the control value.
                    # We expect only one off variation.
                    FeatureStateValue.objects.update_or_create(
                        feature_state=feature_state,
                        defaults={
                            "type": STRING,
                            "string_value": variation_values_by_idx[variation_idx],
                        },
                    )

                mv_feature_option = mv_feature_options_by_variation[variation_idx]
                percentage_allocation = 0

                if variation_config.get("isFallthrough"):
                    # We expect only one fallthrough variation.
                    percentage_allocation = 100

                elif rollout := variation_config.get("rollout"):
                    # 50% allocation is recorded as 50000 in LD.
                    # It's possible to allocate e.g. 50.999, resulting
                    # in rollout == 50999.
                    # Round the values nicely by keeping the `cumulative_rollout` tally.
                    cumulative_rollout += rollout / 1000
                    cumulative_rollout_rounded = round(cumulative_rollout)
                    percentage_allocation = (
                        cumulative_rollout_rounded - rollout_baseline
                    )
                    rollout_baseline = cumulative_rollout_rounded

                MultivariateFeatureStateValue.objects.update_or_create(
                    feature_state=feature_state,
                    multivariate_feature_option=mv_feature_option,
                    defaults={"percentage_allocation": percentage_allocation},
                )

        # TODO: Move target and rule creation to be invoked directly from `process_import_request`.
        # https://github.com/Flagsmith/flagsmith/issues/3383
        _import_targets(
            import_request=import_request,
            ld_flag_config=ld_flag_config,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
            mv_feature_options_by_variation=mv_feature_options_by_variation,
        )
        _import_rules(
            import_request=import_request,
            ld_flag_config=ld_flag_config,
            feature=feature,
            environment=environment,
            segments_by_ld_key=segments_by_ld_key,
            mv_feature_options_by_variation=mv_feature_options_by_variation,
        )


def _get_feature_type_and_feature_state_factory(
    ld_flag: ld_types.FeatureFlag,
) -> Tuple[
    FeatureType,
    Callable[
        [
            LaunchDarklyImportRequest,
            ld_types.FeatureFlag,
            Feature,
            dict[str, Environment],
            dict[str, Segment],
        ],
        None,
    ],
]:
    match ld_flag["kind"]:
        case "multivariate" if len(ld_flag["variations"]) > 2:
            feature_type = MULTIVARIATE
            feature_state_factory = _create_mv_feature_states_with_segments_identities
        case "multivariate":
            feature_type = STANDARD
            feature_state_factory = (
                _create_string_feature_states_with_segments_identities
            )
        case _:  # assume boolean
            feature_type = STANDARD
            feature_state_factory = (
                _create_boolean_feature_states_with_segments_identities
            )

    return feature_type, feature_state_factory


def _create_feature_from_ld(
    import_request: LaunchDarklyImportRequest,
    ld_flag: ld_types.FeatureFlag,
    environments_by_ld_environment_key: dict[str, Environment],
    tags_by_ld_tag: dict[str, Tag],
    segments_by_ld_key: dict[str, Segment],
    project_id: int,
) -> Feature:
    (
        feature_type,
        feature_state_factory,
    ) = _get_feature_type_and_feature_state_factory(
        ld_flag,
    )

    tags = [
        tags_by_ld_tag[LAUNCH_DARKLY_IMPORTED_DEFAULT_TAG_LABEL],
        *(tags_by_ld_tag[ld_tag] for ld_tag in ld_flag["tags"]),
    ]

    feature, _ = Feature.objects.update_or_create(
        project_id=project_id,
        name=ld_flag["key"],
        defaults={
            "description": ld_flag.get("description"),
            "default_enabled": False,
            "type": feature_type,
            "is_archived": ld_flag["archived"],
        },
    )
    feature.tags.set(tags)

    feature_state_factory(
        import_request=import_request,
        ld_flag=ld_flag,
        feature=feature,
        environments_by_ld_environment_key=environments_by_ld_environment_key,
        segments_by_ld_key=segments_by_ld_key,
    )

    return feature


def _create_features_from_ld(
    import_request: LaunchDarklyImportRequest,
    ld_flags: list[ld_types.FeatureFlag],
    environments_by_ld_environment_key: dict[str, Environment],
    tags_by_ld_tag: dict[str, Tag],
    segments_by_ld_key: dict[str, Segment],
    project_id: int,
) -> list[Feature]:
    return [
        _create_feature_from_ld(
            import_request=import_request,
            ld_flag=ld_flag,
            environments_by_ld_environment_key=environments_by_ld_environment_key,
            tags_by_ld_tag=tags_by_ld_tag,
            segments_by_ld_key=segments_by_ld_key,
            project_id=project_id,
        )
        for ld_flag in ld_flags
    ]


def _include_users_to_segment(
    segment: Segment,
    users: list[str],
    negate: bool,
) -> None:
    if len(users) == 0:
        return

    # Find the parent rule of the segment.
    parent_rule, _ = SegmentRule.objects.get_or_create(
        segment=segment, type=SegmentRule.ALL_RULE
    )

    # Create a condition to match against those identities via "key" trait.
    identities_string = ",".join(users)
    included_rule = SegmentRule.objects.create(
        rule=parent_rule,
        type=SegmentRule.NONE_RULE if negate else SegmentRule.ANY_RULE,
    )
    Condition.objects.update_or_create(
        rule=included_rule,
        property="key",
        value=identities_string,
        operator=constants.IN,
        created_with_segment=True,
    )


def _create_segments_from_ld(
    import_request: LaunchDarklyImportRequest,
    ld_segments: list[tuple[ld_types.UserSegment, str]],
    environments_by_ld_environment_key: dict[str, Environment],
    tags_by_ld_tag: dict[str, Tag],
    project_id: int,
) -> dict[str, Segment]:
    """
    Create segments from the given Launch Darkly segments. This also creates inclusion rules for segments.

    :param ld_segments: A list of mapping from (env, segment).
    :return A mapping from ld segment key to Segment itself.
    """
    segments_by_ld_key = {}
    for ld_segment, env in ld_segments:
        if ld_segment["deleted"]:
            continue

        # Make sure consecutive updates do not create the same segment.
        segment, _ = Segment.objects.update_or_create(
            name=_get_segment_name(ld_segment["name"], env),
            project_id=project_id,
        )

        segments_by_ld_key[ld_segment["key"]] = segment

        # TODO: Tagging segments is not supported yet. https://github.com/Flagsmith/flagsmith/issues/3241

        # Create the segment rule for the segment.
        rules = ld_segment["rules"]
        for rule in rules:
            _create_segment_rule_for_segment(
                import_request=import_request,
                segment=segment,
                clauses=rule["clauses"],
            )

        # Create or update identities that are mentioned in the segment.
        for identifier in ld_segment["included"] + ld_segment["excluded"]:
            identity, _ = Identity.objects.get_or_create(
                identifier=identifier,
                environment=environments_by_ld_environment_key[env],
            )
            identity.update_traits(
                [
                    {
                        "trait_key": "key",
                        "trait_value": identifier,
                    }
                ]
            )

        _include_users_to_segment(segment, ld_segment["included"], False)
        _include_users_to_segment(segment, ld_segment["excluded"], True)

        if (
            len(ld_segment["includedContexts"]) > 0
            or len(ld_segment["excludedContexts"]) > 0
        ):
            _log_error(
                import_request=import_request,
                error_message=f"Contexts are not supported, skipping contexts for segment: {segment.name}",
            )

        # Create an empty rule if there are no rules. This is required to create an "SegmentRule" object.
        # Otherwise, UI fails to display the segment.
        SegmentRule.objects.get_or_create(segment=segment, type=SegmentRule.ALL_RULE)

    return segments_by_ld_key


def create_import_request(
    project: "Project",
    user: "FFAdminUser",
    ld_project_key: str,
    ld_token: str,
) -> LaunchDarklyImportRequest:
    ld_client = LaunchDarklyClient(ld_token)

    ld_project = ld_client.get_project(project_key=ld_project_key)
    requested_flag_count = ld_client.get_flag_count(project_key=ld_project_key)

    status: LaunchDarklyImportStatus = {
        "requested_environment_count": ld_project["environments"]["totalCount"],
        "requested_flag_count": requested_flag_count,
        "error_messages": [],
    }

    return LaunchDarklyImportRequest.objects.create(
        project=project,
        created_by=user,
        ld_project_key=ld_project_key,
        ld_token=_sign_ld_value(ld_token, user.id),
        status=status,
    )


def process_import_request(
    import_request: LaunchDarklyImportRequest,
) -> None:
    with _complete_import_request(import_request):
        ld_token = _unsign_ld_value(
            import_request.ld_token,
            import_request.created_by.id,
        )
        ld_project_key = import_request.ld_project_key

        ld_client = LaunchDarklyClient(ld_token)

        try:
            ld_environments = ld_client.get_environments(project_key=ld_project_key)
            ld_flags = ld_client.get_flags(project_key=ld_project_key)
            ld_flag_tags = ld_client.get_flag_tags()
            # ld_segment_tags = ld_client.get_segment_tags()
            # Keyed by (segment, environment)
            ld_segments: list[tuple[ld_types.UserSegment, str]] = []
            for env in ld_environments:
                ld_segments_for_env = ld_client.get_segments(
                    project_key=ld_project_key,
                    environment_key=env["key"],
                )
                for segment in ld_segments_for_env:
                    ld_segments.append((segment, env["key"]))

        except RequestException as exc:
            _log_error(
                import_request=import_request,
                error_message=(
                    f"{exc.__class__.__name__} "
                    f"{str(exc.response.status_code) + ' ' if exc.response else ''}"
                    f"when requesting {exc.request.path_url}"
                ),
            )
            raise

        # Create environments
        environments_by_ld_environment_key = _create_environments_from_ld(
            ld_environments=ld_environments,
            project_id=import_request.project_id,
        )

        # Create segments using `ld_segment_tags`
        # TODO populate with LD tags when https://github.com/Flagsmith/flagsmith/issues/3241 is done
        segment_tags_by_ld_tag = {}
        segments_by_ld_key = _create_segments_from_ld(
            import_request=import_request,
            ld_segments=ld_segments,
            environments_by_ld_environment_key=environments_by_ld_environment_key,
            tags_by_ld_tag=segment_tags_by_ld_tag,
            project_id=import_request.project_id,
        )

        # Create flags
        flag_tags_by_ld_tag = _create_tags_from_ld(
            ld_tags=ld_flag_tags,
            project_id=import_request.project_id,
        )
        _create_features_from_ld(
            import_request=import_request,
            ld_flags=ld_flags,
            environments_by_ld_environment_key=environments_by_ld_environment_key,
            tags_by_ld_tag=flag_tags_by_ld_tag,
            segments_by_ld_key=segments_by_ld_key,
            project_id=import_request.project_id,
        )
