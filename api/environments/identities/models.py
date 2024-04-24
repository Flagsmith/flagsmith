import typing

from django.db import models
from django.db.models import Prefetch, Q
from django.utils import timezone
from flag_engine.segments.evaluator import evaluate_identity_in_segment

from environments.identities.managers import IdentityManager
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from segments.models import Segment
from util.mappers.engine import (
    map_identity_to_engine,
    map_segment_to_engine,
    map_traits_to_engine,
)


class Identity(models.Model):
    identifier = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    environment = models.ForeignKey(
        Environment, related_name="identities", on_delete=models.CASCADE
    )

    objects = IdentityManager()

    class Meta:
        verbose_name_plural = "Identities"
        ordering = ["id"]
        unique_together = ("environment", "identifier")
        # hard code the table name after moving from the environments app to prevent
        # issues with production deployment due to multi server configuration.
        db_table = "environments_identity"
        # Note that the environment / created_date index is added only to postgres, so we can add it concurrently to
        # avoid any downtime. If people using MySQL / Oracle have issues with poor performance on the identities table,
        # we can provide them the SQL to add it manually in a small window of downtime.
        index_together = (("environment", "created_date"),)

    def natural_key(self):
        return self.identifier, self.environment.api_key

    @property
    def composite_key(self):
        return f"{self.environment.api_key}_{self.identifier}"

    def get_hash_key(self, use_identity_composite_key_for_hashing: bool = False) -> str:
        return (
            self.composite_key
            if use_identity_composite_key_for_hashing
            else str(self.id)
        )

    def get_all_feature_states(
        self,
        traits: list[Trait] | None = None,
        additional_filters: Q | None = None,
    ) -> list[FeatureState]:
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
        segments = self.get_segments(traits=traits, overrides_only=True)

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

        if self.environment.use_v2_feature_versioning:
            full_query &= Q(
                Q(identity=self)  # identity overrides are not versioned
                | Q(
                    environment_feature_version__live_from__isnull=False,
                    environment_feature_version__live_from__lte=timezone.now(),
                ),
            )
        else:
            full_query &= Q(live_from__lte=timezone.now(), version__isnull=False)

        if additional_filters:
            full_query &= additional_filters

        select_related_args = [
            "environment",
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
                current_flag = identity_flags[flag.feature_id]
                if flag > current_flag:
                    identity_flags[flag.feature_id] = flag

        if self.environment.get_hide_disabled_flags() is True:
            # filter out any flags that are disabled
            return [value for value in identity_flags.values() if value.enabled]

        return list(identity_flags.values())

    def get_overridden_feature_states(self) -> dict[int, FeatureState]:
        """
        Get all overridden feature states for an identity.

        :return: dict[int, FeatureState] - Key: feature ID. Value: Overridden feature_state.
        """

        return {fs.feature_id: fs for fs in self.identity_features.all()}

    def get_segments(
        self, traits: typing.List[Trait] = None, overrides_only: bool = False
    ) -> typing.List[Segment]:
        """
        Get the list of segments this identity is a part of.

        :param traits: override the identity's traits when evaluating segments
        :param overrides_only: only retrieve the segments which have a valid override in the environment
        :return: List of matching segments
        """
        matching_segments = []
        traits = self.identity_traits.all() if traits is None else traits

        if overrides_only:
            all_segments = self.environment.get_segments_from_cache()
        else:
            all_segments = self.environment.project.get_segments_from_cache()

        engine_identity = map_identity_to_engine(
            self,
            with_overrides=False,
            with_traits=False,
        )
        engine_traits = map_traits_to_engine(traits)

        for segment in all_segments:
            engine_segment = map_segment_to_engine(segment)

            if evaluate_identity_in_segment(
                identity=engine_identity,
                segment=engine_segment,
                override_traits=engine_traits,
            ):
                matching_segments.append(segment)

        return matching_segments

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

        # Remove traits having Null(None) values
        trait_data_items = filter(
            lambda trait: trait["trait_value"] is not None, trait_data_items
        )
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
        current_traits = {t.trait_key: t for t in self.identity_traits.all()}

        keys_to_delete = []
        new_traits = []
        updated_traits = []

        for trait_data_item in trait_data_items:
            trait_key = trait_data_item["trait_key"]
            trait_value = trait_data_item["trait_value"]

            if trait_value is None:
                # build a list of trait keys to delete having been nulled by the
                # input data
                keys_to_delete.append(trait_key)
                continue

            trait_value_data = Trait.generate_trait_value_data(trait_value)

            if trait_key in current_traits:
                current_trait = current_traits[trait_key]
                # Don't update the trait if the value hasn't changed
                if current_trait.trait_value == trait_value:
                    continue

                for attr, value in trait_value_data.items():
                    setattr(current_trait, attr, value)
                updated_traits.append(current_trait)
            else:
                new_traits.append(
                    Trait(**trait_value_data, trait_key=trait_key, identity=self)
                )

        # delete the traits that had their keys set to None
        if keys_to_delete:
            self.identity_traits.filter(trait_key__in=keys_to_delete).delete()

        Trait.objects.bulk_update(updated_traits, fields=Trait.BULK_UPDATE_FIELDS)

        # use ignore_conflicts to handle race conditions which result in IntegrityError if another request
        # has added a particular trait_key for the identity while this method has been determining what to
        # update or create.
        # See: https://github.com/Flagsmith/flagsmith/issues/370
        Trait.objects.bulk_create(new_traits, ignore_conflicts=True)

        # return the full list of traits for this identity by refreshing from the db
        # TODO: handle this in the above logic to avoid a second hit to the DB
        return self.identity_traits.all()
