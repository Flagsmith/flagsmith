import copy
import typing

from django.utils import timezone
from flag_engine.features.models import FeatureModel as EngineFeatureModel
from flag_engine.features.models import FeatureStateModel as EngineFeatureStateModel
from flag_engine.features.models import (
    MultivariateFeatureOptionModel as EngineMultivariateFeatureOptionModel,
)
from flag_engine.features.models import (
    MultivariateFeatureStateValueModel as EngineMultivariateFeatureStateValueModel,
)
from flag_engine.identities.models import IdentityModel as EngineIdentity
from flag_engine.utils.exceptions import DuplicateFeatureState
from pydantic import ValidationError as PydanticValidationError
from pyngo import drf_error_details
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from environments.dynamodb.types import IdentityOverrideV2
from environments.models import Environment
from features.models import Feature, FeatureState, FeatureStateValue
from features.multivariate.models import MultivariateFeatureOption
from features.serializers import (  # type: ignore[attr-defined]
    FeatureStateValueSerializer,
)
from features.value_types import ValueType
from util.mappers import (
    map_engine_identity_to_identity_document,
    map_feature_to_engine,
    map_mv_option_to_engine,
)
from webhooks.constants import WEBHOOK_DATETIME_FORMAT

from .models import EdgeIdentity
from .search import (
    DASHBOARD_ALIAS_ATTRIBUTE,
    DASHBOARD_ALIAS_SEARCH_PREFIX,
    IDENTIFIER_ATTRIBUTE,
    EdgeIdentitySearchData,
    EdgeIdentitySearchType,
)
from .tasks import call_environment_webhook_for_feature_state_change


class LowerCaseCharField(serializers.CharField):
    def to_representation(self, value: typing.Any) -> str:
        return super().to_representation(value).lower()

    def to_internal_value(self, data: typing.Any) -> str:
        return super().to_internal_value(data).lower()


class EdgeIdentitySerializer(serializers.Serializer):  # type: ignore[type-arg]
    identity_uuid = serializers.CharField(read_only=True)
    identifier = serializers.CharField(required=True, max_length=2000)
    dashboard_alias = LowerCaseCharField(
        required=False,
        max_length=100,
    )

    def create(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        identifier = self.validated_data.get("identifier")
        dashboard_alias = self.validated_data.get("dashboard_alias")
        environment_api_key = self.context["view"].kwargs["environment_api_key"]
        self.instance = EngineIdentity(
            identifier=identifier,
            environment_api_key=environment_api_key,
            dashboard_alias=dashboard_alias,
        )
        if EdgeIdentity.dynamo_wrapper.get_item(self.instance.composite_key):
            raise ValidationError(
                f"Identity with identifier: {identifier} already exists"
            )
        EdgeIdentity.dynamo_wrapper.put_item(
            map_engine_identity_to_identity_document(self.instance)
        )
        return self.instance


class EdgeIdentityUpdateSerializer(EdgeIdentitySerializer):
    def get_fields(self):  # type: ignore[no-untyped-def]
        fields = super().get_fields()
        fields["identifier"].read_only = True
        return fields

    def update(
        self, instance: EdgeIdentity, validated_data: dict[str, typing.Any]
    ) -> EdgeIdentity:
        instance.dashboard_alias = (
            self.validated_data.get("dashboard_alias") or instance.dashboard_alias
        )
        instance.save()
        return instance


class EdgeMultivariateFeatureOptionField(serializers.IntegerField):
    def to_internal_value(  # type: ignore[override]
        self,
        data: typing.Any,
    ) -> EngineMultivariateFeatureOptionModel:
        data = super().to_internal_value(data)
        return map_mv_option_to_engine(MultivariateFeatureOption.objects.get(id=data))

    def to_representation(self, obj):  # type: ignore[no-untyped-def]
        return obj.id


class EdgeMultivariateFeatureStateValueSerializer(serializers.Serializer):  # type: ignore[type-arg]
    multivariate_feature_option = EdgeMultivariateFeatureOptionField()
    percentage_allocation = serializers.FloatField(max_value=100, min_value=0)

    def to_internal_value(self, data):  # type: ignore[no-untyped-def]
        data = super().to_internal_value(data)
        return EngineMultivariateFeatureStateValueModel(**data)


class FeatureStateValueEdgeIdentityField(serializers.Field):  # type: ignore[type-arg]
    def to_representation(self, obj):  # type: ignore[no-untyped-def]
        identity: EdgeIdentity = self.parent.context["identity"]
        environment: Environment = self.parent.context["environment"]
        identity_id = identity.get_hash_key(
            environment.use_identity_composite_key_for_hashing
        )

        return obj.get_value(identity_id=identity_id)

    def get_attribute(self, instance):  # type: ignore[no-untyped-def]
        # We pass the object instance onto `to_representation`,
        # not just the field attribute.
        return instance

    def to_internal_value(self, data):  # type: ignore[no-untyped-def]
        fsv_type = ValueType.from_any(data, exclude_types=[ValueType.FLOAT])
        feature_state_value_dict = {
            "type": fsv_type.value,
            FeatureState.get_feature_state_key_name(fsv_type): data,
        }
        fs_value_serializer = FeatureStateValueSerializer(data=feature_state_value_dict)
        fs_value_serializer.is_valid(raise_exception=True)
        return FeatureStateValue(**feature_state_value_dict).value


class EdgeFeatureField(serializers.Field):  # type: ignore[type-arg]
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        help_text = "ID(integer) or name(string) of the feature"
        kwargs.setdefault("help_text", help_text)

        return super().__init__(*args, **kwargs)

    def to_representation(self, obj: Feature) -> int:
        return obj.id

    def to_internal_value(self, data: typing.Union[int, str]) -> EngineFeatureModel:
        if isinstance(data, int):
            return map_feature_to_engine(Feature.objects.get(id=data))

        environment = Environment.objects.get(
            api_key=self.context["view"].kwargs["environment_api_key"]
        )
        return map_feature_to_engine(
            Feature.objects.get(
                name=data,
                project=environment.project,
            )
        )

    class Meta:
        swagger_schema_fields = {"type": "integer/string"}


class BaseEdgeIdentityFeatureStateSerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature_state_value = FeatureStateValueEdgeIdentityField(
        allow_null=True, required=False, default=None
    )
    feature = EdgeFeatureField()  # type: ignore[no-untyped-call]
    multivariate_feature_state_values = EdgeMultivariateFeatureStateValueSerializer(
        many=True, required=False
    )
    enabled = serializers.BooleanField(required=False, default=False)
    featurestate_uuid = serializers.CharField(required=False, read_only=True)

    def save(self, **kwargs):  # type: ignore[no-untyped-def]
        view = self.context["view"]
        request = self.context["request"]

        identity: EdgeIdentity = view.identity
        feature_state_value = self.validated_data.get("feature_state_value", None)

        previous_state = copy.deepcopy(self.instance)

        if not self.instance:
            try:
                self.instance = EngineFeatureStateModel.parse_obj(self.validated_data)
            except PydanticValidationError as exc:
                raise ValidationError(drf_error_details(exc))
            try:
                identity.add_feature_override(self.instance)
            except DuplicateFeatureState as e:
                raise serializers.ValidationError(
                    "Feature state already exists."
                ) from e

        self.instance.set_value(feature_state_value)
        self.instance.enabled = self.validated_data.get(
            "enabled", self.instance.enabled
        )
        self.instance.multivariate_feature_state_values = self.validated_data.get(
            "multivariate_feature_state_values",
            self.instance.multivariate_feature_state_values,
        )

        identity.save(user=request.user)

        new_value = self.instance.get_value(identity.id)
        previous_value = (
            previous_state.get_value(identity.id) if previous_state else None
        )

        # TODO:
        #  - move this logic to the EdgeIdentity model
        call_environment_webhook_for_feature_state_change.delay(
            kwargs={
                "feature_id": self.instance.feature.id,
                "environment_api_key": identity.environment_api_key,
                "identity_id": identity.id,
                "identity_identifier": identity.identifier,
                "changed_by": str(request.user),
                "new_enabled_state": self.instance.enabled,
                "new_value": new_value,
                "previous_enabled_state": getattr(previous_state, "enabled", None),
                "previous_value": previous_value,
                "timestamp": timezone.now().strftime(WEBHOOK_DATETIME_FORMAT),
            },
        )

        return self.instance


class EdgeIdentityFeatureStateSerializer(BaseEdgeIdentityFeatureStateSerializer):
    identity_uuid = serializers.SerializerMethodField()

    def get_identity_uuid(self, obj=None):  # type: ignore[no-untyped-def]
        return self.context["view"].identity.identity_uuid


class EdgeIdentityIdentifierSerializer(serializers.Serializer):  # type: ignore[type-arg]
    identifier = serializers.CharField(required=True, max_length=2000)


# NOTE: This is only used for generating swagger docs
class EdgeIdentityWithIdentifierFeatureStateRequestBody(
    EdgeIdentityFeatureStateSerializer, EdgeIdentityIdentifierSerializer
):
    pass


# NOTE: This is only used for generating swagger docs
class EdgeIdentityWithIdentifierFeatureStateDeleteRequestBody(
    EdgeIdentityIdentifierSerializer
):
    feature = EdgeFeatureField()  # type: ignore[no-untyped-call]


class EdgeIdentityTraitsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    trait_key = serializers.CharField()
    trait_value = serializers.CharField(allow_null=True)


class EdgeIdentityFsQueryparamSerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature = serializers.IntegerField(
        required=False, help_text="ID of the feature to filter by"
    )


class GetEdgeIdentityOverridesQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    feature = serializers.IntegerField(required=False)


class EdgeIdentitySearchField(serializers.CharField):
    def to_internal_value(self, data: str) -> EdgeIdentitySearchData:  # type: ignore[override]
        kwargs = {}
        search_term = data

        if search_term.startswith(DASHBOARD_ALIAS_SEARCH_PREFIX):
            kwargs["search_attribute"] = DASHBOARD_ALIAS_ATTRIBUTE
            # dashboard aliases are always stored in lower case
            search_term = search_term.removeprefix(
                DASHBOARD_ALIAS_SEARCH_PREFIX
            ).lower()
        else:
            kwargs["search_attribute"] = IDENTIFIER_ATTRIBUTE

        if search_term.startswith('"') and search_term.endswith('"'):
            kwargs["search_type"] = EdgeIdentitySearchType.EQUAL  # type: ignore[assignment]
            search_term = search_term[1:-1]
        else:
            kwargs["search_type"] = EdgeIdentitySearchType.BEGINS_WITH  # type: ignore[assignment]

        return EdgeIdentitySearchData(**kwargs, search_term=search_term)  # type: ignore[arg-type]


class ListEdgeIdentitiesQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    page_size = serializers.IntegerField(required=False)
    q = EdgeIdentitySearchField(
        required=False,
        help_text="Search string to look for. Prefix with 'dashboard_alias:' "
        "to search over aliases instead of identifiers.",
    )
    last_evaluated_key = serializers.CharField(required=False, allow_null=True)


class GetEdgeIdentityOverridesResultSerializer(serializers.Serializer):  # type: ignore[type-arg]
    identifier = serializers.CharField()
    identity_uuid = serializers.CharField()
    feature_state = BaseEdgeIdentityFeatureStateSerializer()

    def to_representation(self, instance: IdentityOverrideV2):  # type: ignore[no-untyped-def]
        # Since the FeatureStateValueEdgeIdentityField relies on having this data
        # available to generate the value of the feature state, we need to set this
        # and make it available to the field class. to_representation seems like the
        # best place for this since we only care about serialization here (not
        # deserialization).
        self.context["identity"] = EdgeIdentity.from_identity_document(
            {
                "identifier": instance.identifier,
                "identity_uuid": instance.identity_uuid,
                "environment_api_key": self.context["environment"].api_key,
            }
        )
        return super().to_representation(instance)


class GetEdgeIdentityOverridesSerializer(serializers.Serializer):  # type: ignore[type-arg]
    results = GetEdgeIdentityOverridesResultSerializer(many=True)


class EdgeIdentitySourceIdentityRequestSerializer(serializers.Serializer):  # type: ignore[type-arg]
    source_identity_uuid = serializers.CharField(
        required=True,
        help_text="UUID of the source identity to clone feature states from.",
    )
