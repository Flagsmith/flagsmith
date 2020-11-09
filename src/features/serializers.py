from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from audit.models import AuditLog, RelatedObjectType, FEATURE_CREATED_MESSAGE, FEATURE_UPDATED_MESSAGE, \
    FEATURE_STATE_UPDATED_MESSAGE, IDENTITY_FEATURE_STATE_UPDATED_MESSAGE
from environments.identities.models import Identity
from features.utils import BOOLEAN, INTEGER, STRING
from .fields import FeatureSegmentValueField
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

    def validate(self, attrs):
        # If tags selected check they from the same Project as Feature Project
        if any(tag.project_id != attrs['project'].id for tag in attrs.get('tags', [])):
            raise ValidationError("Selected Tags must be from the same Project as current Feature")

        return attrs


class FeatureSegmentCreateSerializer(serializers.ModelSerializer):
    value = FeatureSegmentValueField(required=False)

    class Meta:
        model = FeatureSegment
        fields = ('id', 'feature', 'segment', 'environment', 'priority', 'enabled', 'value')
        read_only_fields = ('id', 'priority',)

    def create(self, validated_data):
        validated_data['value_type'] = self.context.get('value_type', STRING)
        return super(FeatureSegmentCreateSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data['value_type'] = self.context.get('value_type', STRING)
        return super(FeatureSegmentCreateSerializer, self).update(instance, validated_data)


class FeatureSegmentQuerySerializer(serializers.Serializer):
    environment = serializers.IntegerField()
    feature = serializers.IntegerField()


class FeatureSegmentListSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = FeatureSegment
        fields = ('id', 'segment', 'priority', 'environment', 'enabled', 'value')
        read_only_fields = ('id', 'segment', 'priority', 'environment', 'enabled', 'value')

    def get_value(self, instance):
        return instance.get_value()


class FeatureSegmentChangePrioritiesSerializer(serializers.Serializer):
    priority = serializers.IntegerField(min_value=0, help_text="Value to change the feature segment's priority to.")
    id = serializers.IntegerField()

    def create(self, validated_data):
        try:
            instance = FeatureSegment.objects.get(id=validated_data['id'])
            return self.update(instance, validated_data)
        except FeatureSegment.DoesNotExist:
            raise ValidationError("No feature segment exists with id: %s" % validated_data['id'])

    def update(self, instance, validated_data):
        instance.to(validated_data['priority'])
        return instance


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = (
            "id",
            "name",
            "created_date",
            "description",
            "initial_value",
            "default_enabled",
            "type"
        )
        writeonly_fields = ("initial_value", "default_enabled")


class FeatureWithTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = (
            "id",
            "name",
            "created_date",
            "initial_value",
            "description",
            "default_enabled",
            "type",
            "tags"
        )
        writeonly_fields = (
            "initial_value", "default_enabled"
        )


class FeatureStateSerializerFull(serializers.ModelSerializer):
    feature = FeatureSerializer()
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

    def validate(self, attrs):
        if attrs.get('identity') and attrs.get('environment'):
            if not attrs['identity'].environment == attrs['environment']:
                raise ValidationError("Identity does not exist in environment.")
        return attrs


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
