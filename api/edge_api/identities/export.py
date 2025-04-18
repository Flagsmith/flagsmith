import logging
import typing
import uuid
from decimal import Decimal

from django.utils import timezone
from flag_engine.identities.traits.types import map_any_value_to_trait_value

from edge_api.identities.models import EdgeIdentity
from environments.identities.traits.models import Trait
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import ValueType

EXPORT_EDGE_IDENTITY_PAGINATION_LIMIT = 20000

logger = logging.getLogger()


def export_edge_identity_and_overrides(  # noqa: C901
    environment_api_key: str,
) -> tuple[list, list, list]:  # type: ignore[type-arg]
    kwargs = {
        "environment_api_key": environment_api_key,
        "limit": EXPORT_EDGE_IDENTITY_PAGINATION_LIMIT,
    }
    identity_export = []
    traits_export = []
    identity_override_export = []

    feature_id_to_uuid: dict[int, str] = get_feature_uuid_cache(environment_api_key)
    mv_feature_option_id_to_uuid: dict[int, str] = get_mv_feature_option_uuid_cache(
        environment_api_key
    )
    while True:
        response = EdgeIdentity.dynamo_wrapper.get_all_items(**kwargs)  # type: ignore[arg-type]
        for item in response["Items"]:
            identifier = item["identifier"]
            # export identity
            identity_export.append(
                export_edge_identity(
                    identifier,  # type: ignore[arg-type]
                    environment_api_key,
                    item["created_date"],  # type: ignore[arg-type]
                )
            )
            # export traits
            for trait in item["identity_traits"]:  # type: ignore[union-attr]
                traits_export.append(
                    export_edge_trait(trait, identifier, environment_api_key)  # type: ignore[arg-type]
                )
            for override in item["identity_features"]:  # type: ignore[union-attr]
                featurestate_uuid = override["featurestate_uuid"]  # type: ignore[call-overload,index]
                feature_id = override["feature"]["id"]  # type: ignore[call-overload,index]
                if feature_id not in feature_id_to_uuid:
                    logging.warning("Feature with id %s does not exist", feature_id)
                    continue

                feature_uuid = feature_id_to_uuid[feature_id]  # type: ignore[index]

                # export feature state
                identity_override_export.append(
                    export_edge_feature_state(
                        identifier,  # type: ignore[arg-type]
                        environment_api_key,
                        featurestate_uuid,
                        feature_uuid,
                        override["enabled"],  # type: ignore[arg-type,call-overload,index]
                    )
                )

                # We always want to create the FeatureStateValue, but if there is none in the
                # dynamo object, we just create a default object with a value of null.
                featurestate_value = override.get("feature_state_value")  # type: ignore[union-attr]
                identity_override_export.append(
                    export_featurestate_value(featurestate_value, featurestate_uuid)
                )

                if mvfsv_overrides := override.get("multivariate_feature_state_values"):  # type: ignore[union-attr]
                    for mvfsv_override in mvfsv_overrides:
                        mv_feature_option_id = mvfsv_override[
                            "multivariate_feature_option"
                        ]["id"]
                        if mv_feature_option_id not in mv_feature_option_id_to_uuid:
                            logging.warning(
                                "MultivariateFeatureOption with id %s does not exist",
                                mv_feature_option_id,
                            )
                            continue

                        mv_feature_option_uuid = mv_feature_option_id_to_uuid[
                            mv_feature_option_id
                        ]
                        percentage_allocation = float(
                            mvfsv_override["percentage_allocation"]
                        )
                        # export mv feature state value
                        identity_override_export.append(
                            export_mv_featurestate_value(
                                featurestate_uuid,
                                mv_feature_option_uuid,  # type: ignore[arg-type]
                                percentage_allocation,
                            )
                        )
        if "LastEvaluatedKey" not in response:
            break
        kwargs["start_key"] = response["LastEvaluatedKey"]
    return identity_export, traits_export, identity_override_export


def get_feature_uuid_cache(environment_api_key: str) -> dict[int, str]:
    qs = Feature.objects.filter(
        project__environments__api_key=environment_api_key
    ).values_list("id", "uuid")
    return {feature_id: feature_uuid for feature_id, feature_uuid in qs}


def get_mv_feature_option_uuid_cache(environment_api_key: str) -> dict[int, str]:
    qs = MultivariateFeatureOption.objects.filter(
        feature__project__environments__api_key=environment_api_key
    ).values_list("id", "uuid")
    return {mvfso_id: mvfso_uuid for mvfso_id, mvfso_uuid in qs}


def export_edge_trait(trait: dict, identifier: str, environment_api_key: str) -> dict:  # type: ignore[type-arg]
    trait_value = map_any_value_to_trait_value(trait["trait_value"])
    trait_value_data = Trait.generate_trait_value_data(trait_value)
    return {
        "model": "traits.trait",
        "fields": {
            "identity": [identifier, environment_api_key],
            "created_date": timezone.now().isoformat(),
            "trait_key": trait["trait_key"],
            **trait_value_data,
        },
    }


def export_edge_identity(
    identifier: str, environment_api_key: str, created_date: str
) -> dict:  # type: ignore[type-arg]
    return {
        "model": "identities.identity",
        "fields": {
            "identifier": identifier,
            "created_date": created_date,
            "environment": [environment_api_key],
        },
    }


def export_edge_feature_state(
    identifier: str,
    environment_api_key: str,
    featurestate_uuid: str,
    feature_uuid: str,
    enabled: bool,
) -> dict:  # type: ignore[type-arg]
    # NOTE: All of the datetime columns are not part of
    # dynamo but are part of the django model
    # hence we are setting them to current time
    return {
        "model": "features.featurestate",
        "fields": {
            "uuid": featurestate_uuid,
            "created_at": timezone.now().isoformat(),
            "updated_at": timezone.now().isoformat(),
            "live_from": timezone.now().isoformat(),
            "feature": [feature_uuid],
            "environment": [environment_api_key],
            "identity": [
                identifier,
                environment_api_key,
            ],
            "feature_segment": None,
            "enabled": enabled,
            "version": 1,
        },
    }


def export_featurestate_value(
    featurestate_value: typing.Any, featurestate_uuid: str
) -> dict:  # type: ignore[type-arg]
    if isinstance(featurestate_value, Decimal):
        if featurestate_value.as_tuple().exponent == 0:
            featurestate_value = int(featurestate_value)

    value_type = ValueType.from_any(featurestate_value)
    value_key_name = FeatureState.get_feature_state_key_name(value_type)

    return {
        "model": "features.featurestatevalue",
        "fields": {
            "uuid": uuid.uuid4(),
            "feature_state": [featurestate_uuid],
            "type": value_type.value,
            value_key_name: featurestate_value,
        },
    }


def export_mv_featurestate_value(
    featurestate_uuid: str, mv_feature_option_uuid: int, percentage_allocation: float
) -> dict:  # type: ignore[type-arg]
    return {
        "model": "multivariate.multivariatefeaturestatevalue",
        "fields": {
            "uuid": uuid.uuid4(),
            "feature_state": [featurestate_uuid],
            "multivariate_feature_option": [mv_feature_option_uuid],
            "percentage_allocation": percentage_allocation,
        },
    }
