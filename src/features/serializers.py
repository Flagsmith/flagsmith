from rest_framework import serializers

from audit.models import AuditLog, RelatedObjectType, FEATURE_CREATED_MESSAGE, FEATURE_UPDATED_MESSAGE, \
    FEATURE_STATE_UPDATED_MESSAGE, IDENTITY_FEATURE_STATE_UPDATED_MESSAGE
from segments.serializers import SegmentSerializerBasic
from .models import Feature, FeatureState, FeatureStateValue, FeatureSegment


class CreateFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = "__all__"
        read_only_fields = ('feature_segments',)

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
        fields = ('feature', 'segment', 'priority', 'enabled')


class FeatureSegmentSerializer(serializers.ModelSerializer):
    segment = SegmentSerializerBasic()

    class Meta:
        model = FeatureSegment
        fields = ('segment', 'priority', 'enabled')


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
