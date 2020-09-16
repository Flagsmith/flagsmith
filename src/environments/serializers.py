from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError

from audit.models import ENVIRONMENT_CREATED_MESSAGE, ENVIRONMENT_UPDATED_MESSAGE, RelatedObjectType, AuditLog
from environments.fields import TraitValueField
from environments.models import Environment, Identity, Trait, INTEGER, Webhook, STRING, BOOLEAN
from features.serializers import FeatureStateSerializerFull
from projects.serializers import ProjectSerializer
from segments.serializers import SegmentSerializerBasic


class EnvironmentSerializerFull(serializers.ModelSerializer):
    feature_states = FeatureStateSerializerFull(many=True)
    project = ProjectSerializer()

    class Meta:
        model = Environment
        fields = ('id', 'name', 'feature_states', 'project', 'api_key')


class EnvironmentSerializerLight(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = ('id', 'name', 'api_key', 'project')
        read_only_fields = ('api_key',)

    def create(self, validated_data):
        instance = super(EnvironmentSerializerLight, self).create(validated_data)
        self._create_audit_log(instance, True)
        return instance

    def update(self, instance, validated_data):
        updated_instance = super(EnvironmentSerializerLight, self).update(instance, validated_data)
        self._create_audit_log(instance, False)
        return updated_instance

    def _create_audit_log(self, instance, created):
        message = (ENVIRONMENT_CREATED_MESSAGE if created else ENVIRONMENT_UPDATED_MESSAGE) % instance.name
        request = self.context.get('request')
        AuditLog.objects.create(author=request.user if request else None,
                                related_object_id=instance.id,
                                related_object_type=RelatedObjectType.ENVIRONMENT.name,
                                environment=instance,
                                project=instance.project,
                                log=message)


class IdentifierOnlyIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ('identifier',)


class IdentitySerializerFull(serializers.ModelSerializer):
    identity_features = FeatureStateSerializerFull(many=True)
    environment = EnvironmentSerializerFull()

    class Meta:
        model = Identity
        fields = ('id', 'identifier', 'identity_features', 'environment')


class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ('id', 'identifier', 'environment')
        read_only_fields = ('id', 'environment')

    def save(self, **kwargs):
        environment = kwargs.get('environment')
        identifier = self.validated_data.get('identifier')
        if Identity.objects.filter(environment=environment, identifier=identifier).exists():
            raise ValidationError(
                {'identifier': "Identity with identifier '%s' already exists in this environment" % identifier})
        return super(IdentitySerializer, self).save(**kwargs)


class TraitSerializerFull(serializers.ModelSerializer):
    identity = IdentitySerializer()
    trait_value = serializers.SerializerMethodField()

    class Meta:
        model = Trait
        fields = "__all__"

    @staticmethod
    def get_trait_value(obj):
        return obj.get_trait_value()


class TraitSerializerBasic(serializers.ModelSerializer):
    trait_value = TraitValueField()

    class Meta:
        model = Trait
        fields = ('id', 'trait_key', 'trait_value')
        read_only_fields = ('id',)


class SDKCreateUpdateTraitSerializer(serializers.ModelSerializer):
    identity = IdentifierOnlyIdentitySerializer()
    trait_value = TraitValueField()
    trait_key = serializers.CharField()

    class Meta:
        model = Trait
        fields = ('identity', 'trait_value', 'trait_key')

    def create(self, validated_data):
        identity = self._get_identity(validated_data['identity']['identifier'])

        trait_key = validated_data['trait_key']
        trait_value = validated_data['trait_value']['value']
        trait_value_type = validated_data['trait_value']['type']

        value_key = Trait.get_trait_value_key_name(trait_value_type)

        defaults = {
            value_key: trait_value,
            'value_type': trait_value_type if trait_value_type in [INTEGER, BOOLEAN] else STRING
        }

        return Trait.objects.update_or_create(identity=identity, trait_key=trait_key, defaults=defaults)[0]

    def _get_identity(self, identifier):
        return Identity.objects.get_or_create(identifier=identifier, environment=self.context['environment'])[0]


class SDKBulkCreateUpdateTraitSerializer(SDKCreateUpdateTraitSerializer):
    trait_value = TraitValueField(allow_null=True)


class IncrementTraitValueSerializer(serializers.Serializer):
    trait_key = serializers.CharField()
    increment_by = serializers.IntegerField(write_only=True)
    identifier = serializers.CharField()
    trait_value = serializers.IntegerField(read_only=True)

    def to_representation(self, instance):
        return {
            'trait_key': instance.trait_key,
            'trait_value': instance.integer_value,
            'identifier': instance.identity.identifier
        }

    def create(self, validated_data):
        trait, _ = Trait.objects.get_or_create(**self._build_query_data(validated_data),
                                               defaults=self._build_default_data())

        if trait.value_type != INTEGER:
            raise exceptions.ValidationError('Trait is not an integer.')

        trait.integer_value += validated_data.get('increment_by')
        trait.save()
        return trait

    def _build_query_data(self, validated_data):
        identity_data = {
            'identifier': validated_data.get('identifier'),
            'environment': self.context.get('request').environment
        }
        identity, _ = Identity.objects.get_or_create(**identity_data)

        return {
            'trait_key': validated_data.get('trait_key'),
            'identity': identity
        }

    def _build_default_data(self):
        return {
            'value_type': INTEGER,
            'integer_value': 0
        }


class TraitKeysSerializer(serializers.Serializer):
    keys = serializers.ListSerializer(child=serializers.CharField())


class DeleteAllTraitKeysSerializer(serializers.Serializer):
    key = serializers.CharField()

    def delete(self):
        environment = self.context.get('environment')
        Trait.objects.filter(identity__environment=environment, trait_key=self.validated_data.get('key')).delete()


class IdentitySerializerWithTraitsAndSegments(serializers.Serializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    flags = FeatureStateSerializerFull(many=True)
    traits = TraitSerializerBasic(many=True)
    segments = SegmentSerializerBasic(many=True)


class WebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Webhook
        fields = ('id', 'url', 'enabled', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class IdentifyWithTraitsSerializer(serializers.Serializer):
    identifier = serializers.CharField(write_only=True, required=True)
    traits = TraitSerializerBasic(required=False, many=True)
    flags = FeatureStateSerializerFull(read_only=True, many=True)

    def create(self, validated_data):
        """
        Create the identity with the associated traits
        (optionally store traits if flag set on org)
        """
        environment = self.context['environment']
        identity, created = Identity.objects.get_or_create(
            identifier=validated_data['identifier'], environment=environment
        )

        if not created and environment.project.organisation.persist_trait_data:
            # if this is an update and we're persisting traits, then we need to
            # partially update any traits and return the full list
            return self.update(instance=identity, validated_data=validated_data)

        # generate traits for the identity and store them if configured to do so
        trait_models = identity.generate_traits(
            validated_data.get('traits', []),
            persist=environment.project.organisation.persist_trait_data
        )

        return {
            "identity": identity,
            "traits": trait_models,
            "flags": identity.get_all_feature_states(traits=trait_models)
        }

    def update(self, instance, validated_data):
        """ partially update any traits and return the full list of traits and flags """
        trait_data_items = validated_data.get('traits', [])
        updated_traits = instance.update_traits(trait_data_items)

        return {
            "identity": instance,
            "traits": updated_traits,
            "flags": instance.get_all_feature_states(traits=updated_traits)
        }
