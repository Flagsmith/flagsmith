import logging
import re
from contextlib import contextmanager
from typing import Callable, Optional, Tuple

from django.core import signing
from django.utils import timezone
from flag_engine.segments import constants
from requests.exceptions import RequestException

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
    import_request.status["error_message"] = error_message


@contextmanager
def _complete_import_request(
    import_request: LaunchDarklyImportRequest,
) -> None:
    """
    Wrap code so the import request always ends up completed.

    If no exception raised, assume successful import.

    In case wrapped code needs to expose an error to the user, it should populate
    `import_request.status["error_message"]` before raising an exception.
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


# Based on: https://docs.launchdarkly.com/sdk/concepts/flag-evaluation-rules#operators
def _ld_operator_to_flagsmith_operator(ld_operator: str) -> Optional[str]:
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


# TODO: Not sure what happens if it is not `IN` and there are multiple values.
def _convert_ld_value(values: list[str], ld_operator: str) -> str:
    match ld_operator:
        case "in":
            return ",".join(values)
        case "endsWith":
            return ".*" + re.escape(values[0])
        case "startsWith":
            return re.escape(values[0]) + ".*"
        case "matches" | "segmentMatch":
            return re.escape(values[0]).replace("\\*", ".*")
        case "contains":
            return ".*" + re.escape(values[0]) + ".*"
        case _:
            return values[0]


def _get_segment_name(name: str, env: str) -> str:
    return f"{name} (Override for {env})"


def _create_feature_segment_from_clauses(
    clauses: list[Clause],
    project: Project,
    feature: Feature,
    environment: Environment,
    segments_by_ld_key: dict[str, Segment],
    name: str,
) -> None:
    if "segmentMatch" in [clause["op"] for clause in clauses]:
        if any(clause["op"] != "segmentMatch" for clause in clauses):
            logger.warning(
                f"Nested segment match is not supported, skipping for {feature.name} in {environment.name}"
            )
            return

        if any(clause["negate"] is True for clause in clauses):
            logger.warning(
                f"Negated segment match is not supported, skipping for {feature.name} in {environment.name}"
            )
            return

        # Complex rules that allow matching segments is not allowed in Flagsmith.
        # We can only emulate a single segment match by enabling the segment rule.
        all_targeted_segments: list[str] = sum(
            [clause["values"] for clause in clauses], []
        )
        for index, targeted_segment_key in enumerate(all_targeted_segments):
            targeted_segment_name = segments_by_ld_key[targeted_segment_key].name
            segment = Segment.objects.get(name=targeted_segment_name, project=project)

            feature_segment, _ = FeatureSegment.objects.update_or_create(
                feature=feature,
                segment=segment,
                environment=environment,
                priority=index,
            )

            # Enable rules by default. In LD, rules are enabled if the flag is on.
            FeatureState.objects.update_or_create(
                feature=feature,
                feature_segment=feature_segment,
                environment=environment,
                defaults={"enabled": True},
            )
        return

    segment = Segment.objects.create(name=name, project=project, feature=feature)

    # A parent rule has two children: one for the regular conditions and multiple for the negated conditions
    # Mathematically, this is equivalent to:
    # any(X, Y, !Z) = any(any(X,Y), none(Z))
    # Or with more parameters,
    # any(X, Y, !Z, !W) = any(any(X,Y), none(Z), none(W))
    # Here, any(X,Y) is the child rule. none(Z) and none(W) are the negated children.
    # Since there is no !X operation in Flagsmith, we wrap negated conditions in a none() rule.
    parent_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ANY_RULE)
    child_rule = SegmentRule.objects.create(rule=parent_rule, type=SegmentRule.ANY_RULE)

    for clause in clauses:
        operator = _ld_operator_to_flagsmith_operator(clause["op"])
        value = _convert_ld_value(clause["values"], clause["op"])
        _property = clause["attribute"]

        if operator is not None:
            if clause["negate"] is True:
                negated_child = SegmentRule.objects.create(
                    rule=parent_rule, type=SegmentRule.NONE_RULE
                )
                rule = negated_child
            else:
                rule = child_rule

            condition, _ = Condition.objects.update_or_create(
                rule=rule,
                property=_property,
                value=value,
                operator=operator,
                created_with_segment=True,
            )
            logger.warning("Condition created: " + str(condition))
        else:
            logger.warning(
                "Can't map launch darkly operator: " + clause["op"] + ", skipping..."
            )

    feature_segment, _ = FeatureSegment.objects.update_or_create(
        feature=feature,
        segment=segment,
        environment=environment,
    )

    # Enable rules by default. In LD, rules are enabled if the flag is on.
    FeatureState.objects.update_or_create(
        feature=feature,
        feature_segment=feature_segment,
        environment=environment,
        defaults={"enabled": True},
    )
    return


def _import_targets(
    ld_flag_config: ld_types.FeatureFlagConfig,
    feature: Feature,
    environment: Environment,
) -> None:
    if "targets" in ld_flag_config:
        logger.warning("Targets: " + str(ld_flag_config["targets"]))

    if "contextTargets" in ld_flag_config:
        logger.warning("Context targets: " + str(ld_flag_config["contextTargets"]))


def _import_rules(
    ld_flag_config: ld_types.FeatureFlagConfig,
    feature: Feature,
    environment: Environment,
    variations_by_idx: dict[str, ld_types.Variation],
    segments_by_ld_key: dict[str, Segment],
) -> None:
    if "rules" in ld_flag_config and len(ld_flag_config["rules"]) > 0:
        logger.warning("Rules: " + str(ld_flag_config["rules"]))
        for index, rule in enumerate(ld_flag_config["rules"]):
            variation = variations_by_idx[str(rule["variation"])]["value"]
            description = rule.get("description", "Unknown")

            logger.warning("Rule found: " + description + " : " + str(variation))
            _create_feature_segment_from_clauses(
                rule["clauses"],
                feature.project,
                feature,
                environment,
                segments_by_ld_key,
                "imported-" + str(index),
            )


def _create_boolean_feature_states(
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
        feature_state, _ = FeatureState.objects.update_or_create(
            feature=feature,
            feature_segment=None,
            environment=environment,
            defaults={"enabled": ld_flag_config["on"]},
        )

        FeatureStateValue.objects.update_or_create(
            feature_state=feature_state,
        )

        _import_targets(ld_flag_config, feature, environment)
        _import_rules(
            ld_flag_config, feature, environment, variations_by_idx, segments_by_ld_key
        )


def _create_string_feature_states(
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

        _import_targets(ld_flag_config, feature, environment)
        _import_rules(
            ld_flag_config, feature, environment, variations_by_idx, segments_by_ld_key
        )


def _create_mv_feature_states(
    ld_flag: ld_types.FeatureFlag,
    feature: Feature,
    environments_by_ld_environment_key: dict[str, Environment],
    segments_by_ld_key: dict[str, Segment],
) -> None:
    variations = ld_flag["variations"]
    variations_by_idx = {
        str(idx): variation for idx, variation in enumerate(variations)
    }
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

        _import_targets(ld_flag_config, feature, environment)
        _import_rules(
            ld_flag_config, feature, environment, variations_by_idx, segments_by_ld_key
        )


def _get_feature_type_and_feature_state_factory(
    ld_flag: ld_types.FeatureFlag,
) -> Tuple[
    FeatureType,
    Callable[[ld_types.FeatureFlag, Feature, dict[str, Environment]], None],
]:
    match ld_flag["kind"]:
        case "multivariate" if len(ld_flag["variations"]) > 2:
            feature_type = MULTIVARIATE
            feature_state_factory = _create_mv_feature_states
        case "multivariate":
            feature_type = STANDARD
            feature_state_factory = _create_string_feature_states
        case _:  # assume boolean
            feature_type = STANDARD
            feature_state_factory = _create_boolean_feature_states

    return feature_type, feature_state_factory


def _create_feature_from_ld(
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
        ld_flag=ld_flag,
        feature=feature,
        environments_by_ld_environment_key=environments_by_ld_environment_key,
        segments_by_ld_key=segments_by_ld_key,
    )

    return feature


def _create_features_from_ld(
    ld_flags: list[ld_types.FeatureFlag],
    environments_by_ld_environment_key: dict[str, Environment],
    tags_by_ld_tag: dict[str, Tag],
    segments_by_ld_key: dict[str, Segment],
    project_id: int,
) -> list[Feature]:
    return [
        _create_feature_from_ld(
            ld_flag=ld_flag,
            environments_by_ld_environment_key=environments_by_ld_environment_key,
            tags_by_ld_tag=tags_by_ld_tag,
            segments_by_ld_key=segments_by_ld_key,
            project_id=project_id,
        )
        for ld_flag in ld_flags
    ]


def _create_segments_from_ld(
    ld_segments: list[tuple[ld_types.UserSegment, str]],
    environments_by_ld_environment_key: dict[str, Environment],
    tags_by_ld_tag: dict[str, Tag],
    project_id: int,
) -> dict[str, Segment]:
    """

    :param ld_segments: A list of mapping from (env, segment).
    :return A mapping from ld segment key to Segment itself.
    """
    segments_by_ld_key = {}
    for ld_segment, env in ld_segments:
        if ld_segment["deleted"]:
            continue

        segment, _ = Segment.objects.update_or_create(
            name=_get_segment_name(ld_segment["name"], env),
            project_id=project_id,
        )

        segments_by_ld_key[ld_segment["key"]] = segment

        # TODO: Tagging segments is not supported yet. https://github.com/Flagsmith/flagsmith/issues/3241

        # TODO: Create rules
        logger.warning("Segment rules: " + str(ld_segment["rules"]))

        # TODO: Import users
        logger.warning("Included segment users: " + str(ld_segment["included"]))
        logger.warning("Excluded segment users: " + str(ld_segment["excluded"]))
        logger.warning("Included context users: " + str(ld_segment["includedContexts"]))
        logger.warning("Excluded context users: " + str(ld_segment["excludedContexts"]))

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
            ld_segment_tags = ld_client.get_segment_tags()
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

        environments_by_ld_environment_key = _create_environments_from_ld(
            ld_environments=ld_environments,
            project_id=import_request.project_id,
        )

        segment_tags_by_ld_tag = _create_tags_from_ld(
            ld_tags=ld_segment_tags,
            project_id=import_request.project_id,
        )
        segments_by_ld_key = _create_segments_from_ld(
            ld_segments=ld_segments,
            environments_by_ld_environment_key=environments_by_ld_environment_key,
            tags_by_ld_tag=segment_tags_by_ld_tag,
            project_id=import_request.project_id,
        )

        flag_tags_by_ld_tag = _create_tags_from_ld(
            ld_tags=ld_flag_tags,
            project_id=import_request.project_id,
        )
        _create_features_from_ld(
            ld_flags=ld_flags,
            environments_by_ld_environment_key=environments_by_ld_environment_key,
            tags_by_ld_tag=flag_tags_by_ld_tag,
            segments_by_ld_key=segments_by_ld_key,
            project_id=import_request.project_id,
        )
