import typing

import boto3
from django.conf import settings
from django.db import models
from django.db.models import Prefetch, Q
from django.utils.encoding import python_2_unicode_compatible
from flag_engine.identities.builders import (
    build_identity_dict,
    build_identity_model,
)

from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue

# Intialize the dynamo client globally
dynamo_identity_table = None
if settings.IDENTITIES_TABLE_NAME_DYNAMO:
    dynamo_identity_table = boto3.resource("dynamodb").Table(
        settings.IDENTITIES_TABLE_NAME_DYNAMO
    )


def is_dynamodb_configured(f):
    def inner(*args, **kwargs):
        if not dynamo_identity_table:
            return
        return f(*args, **kwargs)

    return inner


@python_2_unicode_compatible
class Identity(models.Model):
    identifier = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    environment = models.ForeignKey(
        Environment, related_name="identities", on_delete=models.CASCADE
    )

    class Meta:
        verbose_name_plural = "Identities"
        ordering = ["id"]
        unique_together = ("environment", "identifier")
        # hard code the table name after moving from the environments app to prevent
        # issues with production deployment due to multi server configuration.
        db_table = "environments_identity"

    def get_all_feature_states(self, traits: typing.List[Trait] = None):
        """
        Get all feature states for an identity. This method returns a single flag for
        each feature in the identity's environment's project. The flag returned is the
        correct flag based on the priorities as follows (highest -> lowest):

            1. Identity - flag override for this specific identity
            2. Segment - flag overridden for a segment this identity belongs to
            3. Environment - default value for the environment

        :return: (list) flags for an identity with the correct values based on
            identity / segment priorities
        """
        segments = self.get_segments(traits=traits)

        # define sub queries
        belongs_to_environment_query = Q(environment=self.environment)
        overridden_for_identity_query = Q(identity=self)
        overridden_for_segment_query = Q(
            feature_segment__segment__in=segments,
            feature_segment__environment=self.environment,
        )
        environment_default_query = Q(identity=None, feature_segment=None)

        # define the full query
        full_query = belongs_to_environment_query & (
            overridden_for_identity_query
            | overridden_for_segment_query
            | environment_default_query
        )

        select_related_args = [
            "feature",
            "feature_state_value",
            "feature_segment",
            "feature_segment__segment",
            "identity",
        ]

        all_flags = (
            FeatureState.objects.select_related(*select_related_args)
            .prefetch_related(
                Prefetch(
                    "multivariate_feature_state_values",
                    queryset=MultivariateFeatureStateValue.objects.select_related(
                        "multivariate_feature_option"
                    ),
                )
            )
            .filter(full_query)
        )

        # iterate over all the flags and build a dictionary keyed on feature with the highest priority flag
        # for the given identity as the value.
        identity_flags = {}
        for flag in all_flags:
            if flag.feature_id not in identity_flags:
                identity_flags[flag.feature_id] = flag
            else:
                if flag > identity_flags[flag.feature_id]:
                    identity_flags[flag.feature_id] = flag

        if self.environment.project.hide_disabled_flags:
            # filter out any flags that are disabled if configured on the project
            # Note: done here instead of the DB because of CH1245
            return [value for value in identity_flags.values() if value.enabled]

        return list(identity_flags.values())

    def get_segments(self, traits: typing.List[Trait] = None):
        segments = []
        traits = self.identity_traits.all() if traits is None else traits

        for segment in self.environment.project.get_segments_from_cache():
            if segment.does_identity_match(self, traits=traits):
                segments.append(segment)

        return segments

    def get_all_user_traits(self):
        # this is pointless, we should probably replace all uses with the below code
        return self.identity_traits.all()

    def __str__(self):
        return "Account %s" % self.identifier

    def generate_traits(self, trait_data_items, persist=False):
        """
        Given a list of trait data items, validated by TraitSerializerFull, generate
        a list of TraitModel objects for the given identity.

        :param trait_data_items: list of dictionaries validated by TraitSerializerFull
        :param persist: determines whether the traits should be persisted to db
        :return: list of TraitModels
        """
        trait_models = []
        for trait_data_item in trait_data_items:
            trait_key = trait_data_item["trait_key"]
            trait_value = trait_data_item["trait_value"]
            trait_models.append(
                Trait(
                    trait_key=trait_key,
                    identity=self,
                    **Trait.generate_trait_value_data(trait_value),
                )
            )

        if persist:
            Trait.objects.bulk_create(trait_models)

        return trait_models

    def update_traits(self, trait_data_items):
        """
        Given a list of traits, update any that already exist and create any new ones.
        Return the full list of traits for the given identity after these changes.

        :param trait_data_items: list of dictionaries validated by TraitSerializerFull
        :return: queryset of updated trait models
        """
        current_traits = self.get_all_user_traits()

        keys_to_delete = []

        for trait_data_item in trait_data_items:
            trait_key = trait_data_item["trait_key"]
            trait_value = trait_data_item["trait_value"]

            if trait_value is None:
                # build a list of trait keys to delete having been nulled by the
                # input data
                keys_to_delete.append(trait_key)
                continue

            trait_value_data = Trait.generate_trait_value_data(trait_value)

            if current_traits.filter(trait_key=trait_key).exists():
                current_trait = current_traits.get(trait_key=trait_key)
                for attr, value in trait_value_data.items():
                    setattr(current_trait, attr, value)
                current_trait.save()
            else:
                # use update_or_create to avoid race condition
                kwargs = {"trait_key": trait_key, "identity": self}
                Trait.objects.update_or_create(defaults=trait_value_data, **kwargs)

        # delete the traits that had their keys set to None
        if keys_to_delete:
            current_traits.filter(trait_key__in=keys_to_delete).delete()

        # return the full list of traits for this identity by refreshing from the db
        # TODO: handle this in the above logic to avoid a second hit to the DB
        return self.get_all_user_traits()

    @staticmethod
    @is_dynamodb_configured
    def bulk_send_to_dynamodb(identities: typing.List["Identity"]):
        with dynamo_identity_table.batch_writer() as batch:
            for identity in identities:
                identity_dict = build_identity_dict(identity)
                batch.put_item(Item=identity_dict)

    @staticmethod
    @is_dynamodb_configured
    def query_items_dynamodb(*args, **kwargs):
        return dynamo_identity_table.query(*args, **kwargs)

    @staticmethod
    @is_dynamodb_configured
    def put_item_dynamodb(identity_obj: typing.Any):
        identity_dict = build_identity_dict(identity_obj)
        dynamo_identity_table.put_item(Item=identity_dict)

    @staticmethod
    @is_dynamodb_configured
    def get_item_dynamodb(key: dict):
        identity_document = dynamo_identity_table.get_item(Key=key)["Item"]
        return build_identity_model(identity_document)

    @staticmethod
    @is_dynamodb_configured
    def delete_in_dynamodb(composite_key: str):
        dynamo_identity_table.delete_item(Key={"composite_key": composite_key})
