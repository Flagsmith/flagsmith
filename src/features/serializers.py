from rest_framework import serializers

from audit.models import AuditLog, RelatedObjectType, FEATURE_CREATED_MESSAGE, FEATURE_UPDATED_MESSAGE, \
    FEATURE_STATE_UPDATED_MESSAGE, IDENTITY_FEATURE_STATE_UPDATED_MESSAGE
from environments.models import Identity
from features.utils import get_value_type, get_boolean_from_string, get_integer_from_string, BOOLEAN, INTEGER
from segments.serializers import SegmentSerializerBasic
from .models import Feature, FeatureState, FeatureStateValue, FeatureSegment


class CreateFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"
        read_only_fields = ('feature_segments',)

    def to_internal_value(self, data):
        if data.get('initial_value'):
            data['initial_value'] = str(data.get('initial_value'))
        return super(CreateFeatureSerializer, self).to_internal_value(data)

    def create(self, validated_data):
        if Feature.objects.filter(project=validated_data['project'], name__iexact=validated_data['name']).exists():
            raise serializers.ValidationError("Feature with that name already exists for this "
                                              "project. Note that feature names are case "
                                              "insensitive.")

        instance = super(CreateFeatureSerializer, self).create(validated_data)

        self._create_audit_log(instance, True)

        return instance

    def update(self, instance, validated_data):
        self._create_audit_log(instance, False)
        return super(CreateFeatureSerializer, self).update(instance, validated_data)

    def _create_audit_log(self, instance, created):
        message = FEATURE_CREATED_MESSAGE % instance.name if created else FEATURE_UPDATED_MESSAGE % instance.name
        request = self.context.get('request')
        AuditLog.objects.create(author=request.user if request else None, related_object_id=instance.id,
                                related_object_type=RelatedObjectType.FEATURE.name,
                                project=instance.project,
                                log=message)


class FeatureSegmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSegment
        fields = ('feature', 'segment', 'priority', 'enabled', 'value')

    def create(self, validated_data):
        if validated_data.get('value') or validated_data.get('value') is False:
            validated_data['value_type'] = get_value_type(validated_data['value'])
        return super(FeatureSegmentCreateSerializer, self).create(validated_data)

    def to_internal_value(self, data):
        if data.get('value') or data.get('value') is False:
            data['value'] = str(data['value'])
        return super(FeatureSegmentCreateSerializer, self).to_internal_value(data)


class FeatureSegmentSerializer(serializers.ModelSerializer):
    segment = SegmentSerializerBasic()
    value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureSegment
        fields = ('segment', 'priority', 'enabled', 'value')

    def get_value(self, instance):
        if instance.value:
            value_type = get_value_type(instance.value)
            if value_type == BOOLEAN:
                return get_boolean_from_string(instance.value)
            elif value_type == INTEGER:
                return get_integer_from_string(instance.value)

        return instance.value


class FeatureSerializer(serializers.ModelSerializer):
    feature_segments = FeatureSegmentSerializer(many=True)

    class Meta:
        model = Feature
        fields = "__all__"


class FeatureStateSerializerFull(serializers.ModelSerializer):
    feature = CreateFeatureSerializer()
    feature_state_value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureState
        fields = "__all__"

    def get_feature_state_value(self, obj):
        return obj.get_feature_state_value()


class FeatureStateSerializerBasic(serializers.ModelSerializer):
    feature_state_value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureState
        fields = "__all__"

    def get_feature_state_value(self, obj):
        return obj.get_feature_state_value()

    def create(self, validated_data):
        instance = super(FeatureStateSerializerBasic, self).create(validated_data)
        self._create_audit_log(instance=instance)
        return instance

    def update(self, instance, validated_data):
        updated_instance = super(FeatureStateSerializerBasic, self).update(instance, validated_data)
        self._create_audit_log(updated_instance)
        return updated_instance

    def _create_audit_log(self, instance):
        create_feature_state_audit_log(instance, self.context.get('request'))


class FeatureStateSerializerWithIdentity(FeatureStateSerializerBasic):
    class _IdentitySerializer(serializers.ModelSerializer):
        class Meta:
            model = Identity
            fields = ('id', 'identifier')

    identity = _IdentitySerializer()


class FeatureStateSerializerFullWithIdentity(FeatureStateSerializerFull):
    identity_identifier = serializers.SerializerMethodField()

    def get_identity_identifier(self, instance):
        return instance.identity.identifier if instance.identity else None


class FeatureStateSerializerCreate(serializers.ModelSerializer):
    class Meta:
        model = FeatureState
        fields = ('feature', 'enabled')

    def create(self, validated_data):
        instance = super(FeatureStateSerializerCreate, self).create(validated_data)
        self._create_audit_log(instance=instance)
        return instance

    def _create_audit_log(self, instance):
        create_feature_state_audit_log(instance, self.context.get('request'))


def create_feature_state_audit_log(feature_state, request):
    if feature_state.identity:
        message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (feature_state.feature.name,
                                                            feature_state.identity.identifier)
    else:
        message = FEATURE_STATE_UPDATED_MESSAGE % feature_state.feature.name

    AuditLog.objects.create(author=request.user if request else None,
                            related_object_id=feature_state.id,
                            related_object_type=RelatedObjectType.FEATURE_STATE.name,
                            environment=feature_state.environment,
                            project=feature_state.environment.project,
                            log=message)


class FeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureStateValue
        fields = "__all__"
