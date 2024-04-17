from __future__ import unicode_literals

import datetime
import logging
import typing
import uuid
from copy import deepcopy

from core.models import (
    AbstractBaseExportableModel,
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from django.core.exceptions import (
    NON_FIELD_ERRORS,
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import models
from django.db.models import Max, Q, QuerySet
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_lifecycle import (
    AFTER_CREATE,
    BEFORE_CREATE,
    BEFORE_SAVE,
    LifecycleModelMixin,
    hook,
)
from ordered_model.models import OrderedModelBase
from simple_history.models import HistoricalRecords

from audit.constants import (
    FEATURE_CREATED_MESSAGE,
    FEATURE_DELETED_MESSAGE,
    FEATURE_STATE_UPDATED_MESSAGE,
    FEATURE_STATE_VALUE_UPDATED_MESSAGE,
    FEATURE_UPDATED_MESSAGE,
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE,
    IDENTITY_FEATURE_STATE_UPDATED_MESSAGE,
    IDENTITY_FEATURE_STATE_VALUE_UPDATED_MESSAGE,
    SEGMENT_FEATURE_STATE_DELETED_MESSAGE,
    SEGMENT_FEATURE_STATE_UPDATED_MESSAGE,
    SEGMENT_FEATURE_STATE_VALUE_UPDATED_MESSAGE,
)
from audit.related_object_type import RelatedObjectType
from audit.tasks import create_segment_priorities_changed_audit_log
from environments.identities.helpers import (
    get_hashed_percentage_for_object_ids,
)
from features.constants import ENVIRONMENT, FEATURE_SEGMENT, IDENTITY
from features.custom_lifecycle import CustomLifecycleModelMixin
from features.feature_states.models import AbstractBaseFeatureValueModel
from features.feature_types import MULTIVARIATE, STANDARD
from features.helpers import get_correctly_typed_value
from features.managers import (
    FeatureManager,
    FeatureSegmentManager,
    FeatureStateManager,
    FeatureStateValueManager,
)
from features.multivariate.models import MultivariateFeatureStateValue
from features.utils import (
    get_boolean_from_string,
    get_integer_from_string,
    get_value_type,
)
from features.value_types import (
    BOOLEAN,
    FEATURE_STATE_VALUE_TYPES,
    INTEGER,
    STRING,
)
from features.versioning.models import EnvironmentFeatureVersion
from projects.models import Project
from projects.tags.models import Tag

from . import audit_helpers

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.models import Environment


class Feature(
    SoftDeleteExportableModel,
    CustomLifecycleModelMixin,
    abstract_base_auditable_model_factory(["uuid"]),
):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    project = models.ForeignKey(
        Project,
        related_name="features",
        help_text=_(
            "Changing the project selected will remove previous Feature States for the previously "
            "associated projects Environments that are related to this Feature. New default "
            "Feature States will be created for the new selected projects Environments for this "
            "Feature. Also this will remove any Tags associated with a feature as Tags are Project defined"
        ),
        # Cascade deletes are decouple from the Django ORM. See this PR for details.
        # https://github.com/Flagsmith/flagsmith/pull/3360/
        on_delete=models.DO_NOTHING,
    )
    initial_value = models.CharField(
        max_length=20000, null=True, default=None, blank=True
    )
    description = models.TextField(null=True, blank=True)
    default_enabled = models.BooleanField(default=False)
    type = models.CharField(max_length=50, blank=True, default=STANDARD)
    tags = models.ManyToManyField(Tag, blank=True)
    is_archived = models.BooleanField(default=False)
    owners = models.ManyToManyField(
        "users.FFAdminUser", related_name="owned_features", blank=True
    )
    group_owners = models.ManyToManyField(
        "users.UserPermissionGroup", related_name="owned_features", blank=True
    )

    is_server_key_only = models.BooleanField(default=False)

    history_record_class_path = "features.models.HistoricalFeature"
    related_object_type = RelatedObjectType.FEATURE

    objects = FeatureManager()

    class Meta:
        # Note: uniqueness index is added in explicit SQL in the migrations (See 0005, 0050)
        # TODO: after upgrade to Django 4.0 use UniqueConstraint()
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    @hook(AFTER_CREATE)
    def create_feature_states(self):
        FeatureState.create_initial_feature_states_for_feature(feature=self)

    def validate_unique(self, *args, **kwargs):
        """
        Checks unique constraints on the model and raises ``ValidationError``
        if any failed.
        """
        super(Feature, self).validate_unique(*args, **kwargs)

        # handle case insensitive names per project, as above check allows it
        if (
            Feature.objects.filter(project=self.project, name__iexact=self.name)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        "Feature with that name already exists for this project. Note that feature "
                        "names are case insensitive.",
                    ],
                }
            )

    def __str__(self):
        return "Project %s - Feature %s" % (self.project.name, self.name)

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        return FEATURE_CREATED_MESSAGE % self.name

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        return FEATURE_DELETED_MESSAGE % self.name

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        return FEATURE_UPDATED_MESSAGE % self.name

    def _get_project(self) -> typing.Optional["Project"]:
        return self.project


def get_next_segment_priority(feature):
    feature_segments = FeatureSegment.objects.filter(feature=feature).order_by(
        "-priority"
    )
    if feature_segments.count() == 0:
        return 1
    else:
        return feature_segments.first().priority + 1


class FeatureSegment(
    AbstractBaseExportableModel,
    OrderedModelBase,
    abstract_base_auditable_model_factory(["uuid"]),
):
    history_record_class_path = "features.models.HistoricalFeatureSegment"
    related_object_type = RelatedObjectType.FEATURE

    feature = models.ForeignKey(
        Feature, on_delete=models.CASCADE, related_name="feature_segments"
    )
    segment = models.ForeignKey(
        "segments.Segment", related_name="feature_segments", on_delete=models.CASCADE
    )
    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="feature_segments",
    )
    environment_feature_version = models.ForeignKey(
        "feature_versioning.EnvironmentFeatureVersion",
        on_delete=models.CASCADE,
        related_name="feature_segments",
        null=True,
        blank=True,
    )

    _enabled = models.BooleanField(
        default=False,
        db_column="enabled",
        help_text="Deprecated in favour of using FeatureStateValue.",
    )
    _value = models.CharField(
        max_length=2000,
        blank=True,
        null=True,
        db_column="value",
        help_text="Deprecated in favour of using FeatureStateValue.",
    )
    _value_type = models.CharField(
        choices=FEATURE_STATE_VALUE_TYPES,
        max_length=50,
        blank=True,
        null=True,
        db_column="value_type",
        help_text="Deprecated in favour of using FeatureStateValue.",
    )

    # specific attributes for managing the order of feature segments
    priority = models.PositiveIntegerField(editable=False, db_index=True)
    order_field_name = "priority"
    order_with_respect_to = ("feature", "environment", "environment_feature_version")

    objects = FeatureSegmentManager()

    class Meta:
        unique_together = (
            "feature",
            "environment",
            "segment",
            "environment_feature_version",
        )
        ordering = ("priority",)

    def __str__(self):
        return (
            "FeatureSegment for "
            + self.feature.name
            + " with priority "
            + str(self.priority)
        )

    def __lt__(self, other):
        """
        Kind of counter intuitive but since priority 1 is highest, we want to check if priority is GREATER than the
        priority of the other feature segment.
        """
        return other and self.priority > other.priority

    def clone(
        self,
        environment: "Environment",
        environment_feature_version: "EnvironmentFeatureVersion" = None,
    ) -> "FeatureSegment":
        clone = deepcopy(self)
        clone.id = None
        clone.uuid = uuid.uuid4()
        clone.environment = environment
        clone.environment_feature_version = environment_feature_version
        clone.save()
        return clone

    # noinspection PyTypeChecker
    def get_value(self):
        return get_correctly_typed_value(self.value_type, self.value)

    @classmethod
    def update_priorities(
        cls,
        new_feature_segment_id_priorities: typing.List[typing.Tuple[int, int]],
    ) -> QuerySet["FeatureSegment"]:
        """
        Method to update the priorities of multiple feature segments at once.

        :param new_feature_segment_id_priorities: a list of 2-tuples containing the id, new priority value of
            the feature segments
        :return: a 3-tuple consisting of:
            - a boolean detailing whether any changes were made
            - a list of 2-tuples containing the id, old priority value of the feature segments
            - a queryset containing the updated feature segment model objects
        """
        feature_segments = cls.objects.filter(
            id__in=[pair[0] for pair in new_feature_segment_id_priorities]
        )

        existing_feature_segment_id_priority_pairs = cls.to_id_priority_tuple_pairs(
            feature_segments
        )

        def sort_function(id_priority_pair):
            priority = id_priority_pair[1]
            return priority

        if sorted(
            existing_feature_segment_id_priority_pairs, key=sort_function
        ) == sorted(new_feature_segment_id_priorities, key=sort_function):
            # no changes needed - do nothing (but return existing feature segments)
            return feature_segments

        id_priority_dict = dict(new_feature_segment_id_priorities)

        for fs in feature_segments:
            new_priority = id_priority_dict[fs.id]
            fs.to(new_priority)

        request = getattr(HistoricalRecords.thread, "request", None)
        if request:
            create_segment_priorities_changed_audit_log.delay(
                kwargs={
                    "previous_id_priority_pairs": existing_feature_segment_id_priority_pairs,
                    "feature_segment_ids": [
                        pair[0] for pair in new_feature_segment_id_priorities
                    ],
                    "user_id": getattr(request.user, "id", None),
                    "master_api_key_id": (
                        request.master_api_key.id
                        if hasattr(request, "master_api_key")
                        else None
                    ),
                    "changed_at": timezone.now().isoformat(),
                }
            )

        # since the `to` method updates the priority in place, we don't need to refresh
        # the objects from the database.
        return feature_segments

    @staticmethod
    def to_id_priority_tuple_pairs(
        feature_segments: typing.Union[
            typing.Iterable["FeatureSegment"], typing.Iterable[dict]
        ]
    ) -> typing.List[typing.Tuple[int, int]]:
        """
        Helper method to convert a collection of FeatureSegment objects or dictionaries to a list of 2-tuples
        consisting of the id, priority of the feature segments.
        """
        id_priority_pairs = []
        for fs in feature_segments:
            if isinstance(fs, dict):
                id_priority_pairs.append((fs["id"], fs["priority"]))
            else:
                id_priority_pairs.append((fs.id, fs.priority))

        return id_priority_pairs

    def get_audit_log_related_object_id(self, history_instance) -> int:
        return self.feature_id

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        return SEGMENT_FEATURE_STATE_DELETED_MESSAGE % (
            self.feature.name,
            self.segment.name,
        )

    def _get_environment(self) -> "Environment":
        return self.environment


class FeatureState(
    SoftDeleteExportableModel,
    LifecycleModelMixin,
    abstract_base_auditable_model_factory(
        historical_records_excluded_fields=["uuid"],
        change_details_excluded_fields=["live_from", "version"],
        show_change_details_for_create=True,
    ),
):
    history_record_class_path = "features.models.HistoricalFeatureState"
    related_object_type = RelatedObjectType.FEATURE_STATE

    feature = models.ForeignKey(
        Feature, related_name="feature_states", on_delete=models.CASCADE
    )

    environment = models.ForeignKey(
        "environments.Environment",
        related_name="feature_states",
        null=True,
        on_delete=models.CASCADE,
    )
    identity = models.ForeignKey(
        "identities.Identity",
        related_name="identity_features",
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
    )
    feature_segment = models.ForeignKey(
        FeatureSegment,
        related_name="feature_states",
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
    )

    enabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    live_from = models.DateTimeField(null=True)

    change_request = models.ForeignKey(
        "workflows_core.ChangeRequest",
        on_delete=models.CASCADE,
        null=True,
        related_name="feature_states",
    )

    objects = FeatureStateManager()

    environment_feature_version = models.ForeignKey(
        "feature_versioning.EnvironmentFeatureVersion",
        on_delete=models.SET_NULL,
        null=True,
        related_name="feature_states",
    )

    # to be deprecated!
    version = models.IntegerField(default=1, null=True)

    class Meta:
        ordering = ["id"]

    # TODO: can we simplify this so we don't need `noqa`?
    def __gt__(self, other: "FeatureState") -> bool:  # noqa: C901
        """
        Checks if the current feature state is higher priority that the provided feature state.

        :param other: (FeatureState) the feature state to compare the priority of
        :return: True if self is higher priority than other
        """
        if self.environment_id != other.environment_id:
            raise ValueError(
                "Cannot compare feature states as they belong to different environments."
            )

        if self.feature_id != other.feature_id:
            raise ValueError(
                "Cannot compare feature states as they belong to different features."
            )

        if self.identity_id:
            # identity is the highest priority so we can always return true
            if other.identity_id and self.identity_id != other.identity_id:
                raise ValueError(
                    "Cannot compare feature states as they are for different identities."
                )
            return True

        if (
            self.feature_segment_id
            and self.feature_segment_id != other.feature_segment_id
        ):
            # Return true if other_feature_state has a lower priority feature segment and not an identity overridden
            # flag, else False.
            return not (
                other.identity_id
                or (
                    other.feature_segment_id
                    and self.feature_segment < other.feature_segment
                )
            )

        if self.type == other.type:
            if self.environment.use_v2_feature_versioning:
                return (
                    self.environment_feature_version > other.environment_feature_version
                )
            else:
                # we use live_from here as a priority over the version since
                # the version is given when change requests are committed,
                # hence the version for a feature state that is scheduled
                # further in the future can be lower than a feature state
                # whose live_from value is earlier.
                # See: https://github.com/Flagsmith/flagsmith/issues/2030
                if self.is_live:
                    if not other.is_live or self.is_more_recent_live_from(other):
                        return True
                    elif (
                        self.live_from == other.live_from
                        and self._is_more_recent_version(other)
                    ):
                        return True

                return False

        # if we've reached here, then self is just the environment default. In this case, other is higher priority if
        # it has a feature_segment or an identity
        return not (other.feature_segment_id or other.identity_id)

    def __str__(self):
        s = f"Feature {self.feature.name} - Enabled: {self.enabled}"
        if self.environment is not None:
            s = f"{self.environment} - {s}"
        elif self.identity is not None:
            s = f"Identity {self.identity.identifier} - {s}"
        return s

    @property
    def previous_feature_state_value(self):
        try:
            history_instance = self.feature_state_value.history.first()
            return (
                history_instance
                and getattr(history_instance, "prev_record", None)
                and history_instance.prev_record.instance.value
            )
        except ObjectDoesNotExist:
            return None

    @property
    def type(self) -> str:
        if self.identity_id and self.feature_segment_id is None:
            return IDENTITY
        elif self.feature_segment_id and self.identity_id is None:
            return FEATURE_SEGMENT
        elif self.identity_id is None and self.feature_segment_id is None:
            return ENVIRONMENT

        logger.error(
            "FeatureState %d does not have a valid type. Defaulting to environment.",
            self.id,
        )
        return ENVIRONMENT

    @property
    def is_live(self) -> bool:
        if self.environment.use_v2_feature_versioning:
            return self.environment_feature_version.is_live
        else:
            return (
                self.version is not None
                and self.live_from is not None
                and self.live_from <= timezone.now()
            )

    @property
    def is_scheduled(self) -> bool:
        return self.live_from and self.live_from > timezone.now()

    def clone(
        self,
        env: "Environment",
        live_from: datetime.datetime = None,
        as_draft: bool = False,
        version: int = None,
        environment_feature_version: "EnvironmentFeatureVersion" = None,
    ) -> "FeatureState":
        # Cloning the Identity is not allowed because they are closely tied
        # to the environment
        assert self.identity is None
        clone = deepcopy(self)
        clone.id = None
        clone.uuid = uuid.uuid4()

        if self.feature_segment:
            # We can only create a new feature segment if we are cloning to another environment,
            # or we are creating the feature segment in a new version (versioning v2). This is
            # due to the default unique constraint on the FeatureSegment model which means that
            # the same feature, segment and environment combination cannot exist more than once.
            clone.feature_segment = (
                self.feature_segment.clone(
                    environment=env,
                    environment_feature_version=environment_feature_version,
                )
                if env != self.environment or environment_feature_version is not None
                else self.feature_segment
            )

        clone.environment = env
        clone.version = None if as_draft else version or self.version
        clone.live_from = live_from
        clone.environment_feature_version = environment_feature_version
        clone.save()
        # clone the related objects
        self.feature_state_value.clone(clone)

        if self.feature.type == MULTIVARIATE:
            mv_values = [
                mv_value.clone(feature_state=clone, persist=False)
                for mv_value in self.multivariate_feature_state_values.all()
            ]
            MultivariateFeatureStateValue.objects.bulk_create(mv_values)

        return clone

    def generate_feature_state_value_data(self, value):
        """
        Takes the value of a feature state to generate a feature state value and returns dictionary
        to use for passing into feature state value serializer

        :param value: feature state value of variable type
        :return: dictionary to pass directly into feature state value serializer
        """
        fsv_type = self.get_feature_state_value_type(value)
        return {
            "type": fsv_type,
            "feature_state": self.id,
            self.get_feature_state_key_name(fsv_type): value,
        }

    def get_feature_state_value_by_hash_key(
        self, identity_hash_key: typing.Union[str, int] = None
    ) -> typing.Any:
        feature_state_value = (
            self.get_multivariate_feature_state_value(identity_hash_key)
            if self.feature.type == MULTIVARIATE and identity_hash_key
            else getattr(self, "feature_state_value", None)
        )

        # return the value of the feature state value only if the feature state
        # has a related feature state value. Note that we use getattr rather than
        # hasattr as we want to return None if no feature state value exists.
        return feature_state_value and feature_state_value.value

    def get_feature_state_value(self, identity: "Identity" = None) -> typing.Any:
        identity_hash_key = (
            identity.get_hash_key(
                identity.environment.use_identity_composite_key_for_hashing
            )
            if identity
            else None
        )
        return self.get_feature_state_value_by_hash_key(identity_hash_key)

    def get_feature_state_value_defaults(self) -> dict:
        if (
            self.feature.initial_value is None
            or self.feature.project.prevent_flag_defaults
        ):
            return {}

        value = self.feature.initial_value
        type = get_value_type(value)
        parse_func = {
            BOOLEAN: get_boolean_from_string,
            INTEGER: get_integer_from_string,
        }.get(type, lambda v: v)
        key_name = self.get_feature_state_key_name(type)

        return {"type": type, key_name: parse_func(value)}

    def get_multivariate_feature_state_value(
        self, identity_hash_key: str
    ) -> AbstractBaseFeatureValueModel:
        # the multivariate_feature_state_values should be prefetched at this point
        # so we just convert them to a list and use python operations from here to
        # avoid further queries to the DB
        mv_options = list(self.multivariate_feature_state_values.all())

        percentage_value = (
            get_hashed_percentage_for_object_ids([self.id, identity_hash_key]) * 100
        )

        # Iterate over the mv options in order of id (so we get the same value each
        # time) to determine the correct value to return to the identity based on
        # the percentage allocations of the multivariate options. This gives us a
        # way to ensure that the same value is returned every time we use the same
        # percentage value.
        start_percentage = 0
        for mv_option in sorted(mv_options, key=lambda o: o.id):
            limit = getattr(mv_option, "percentage_allocation", 0) + start_percentage
            if start_percentage <= percentage_value < limit:
                return mv_option.multivariate_feature_option

            start_percentage = limit

        # if none of the percentage allocations match the percentage value we got for
        # the identity, then we just return the default feature state value (or None
        # if there isn't one - although this should never happen)
        return getattr(self, "feature_state_value", None)

    @hook(BEFORE_CREATE)
    @hook(BEFORE_SAVE, when="deleted", is_not=True)
    def check_for_duplicate_feature_state(self):
        if self.version is None:
            return
        filter_ = Q(
            environment=self.environment,
            feature=self.feature,
            feature_segment=self.feature_segment,
            identity=self.identity,
        )
        if self.id:
            filter_ &= ~Q(id=self.id)

        if self.environment.use_v2_feature_versioning:
            filter_ = filter_ & Q(
                environment_feature_version=self.environment_feature_version
            )
        else:
            filter_ = filter_ & Q(version=self.version)

        if FeatureState.objects.filter(filter_).exists():
            raise ValidationError(
                "Feature state already exists for this environment, feature, "
                "version, segment & identity combination"
            )

    @hook(BEFORE_CREATE)
    def set_live_from(self):
        """
        Set the live_from date on newly created, version 1 feature states to maintain
        the previous behaviour.
        """
        if (
            self.environment.use_v2_feature_versioning is False
            and self.version is not None
            and self.live_from is None
        ):
            self.live_from = timezone.now()

    @hook(AFTER_CREATE)
    def create_feature_state_value(self):
        # note: this is only performed after create since feature state values are
        # updated separately, and hence if this is performed after each save,
        # it overwrites the FSV with the initial value again
        FeatureStateValue.objects.create(
            feature_state=self,
            **self.get_feature_state_value_defaults(),
        )

    @hook(AFTER_CREATE)
    def create_multivariate_feature_state_values(self):
        if not (self.feature_segment or self.identity):
            # we only want to create the multivariate feature state values for
            # feature states related to an environment only, i.e. when a new
            # environment is created or a new MV feature is created
            mv_feature_state_values = [
                MultivariateFeatureStateValue(
                    feature_state=self,
                    multivariate_feature_option=mv_option,
                    percentage_allocation=mv_option.default_percentage_allocation,
                )
                for mv_option in self.feature.multivariate_options.all()
            ]
            MultivariateFeatureStateValue.objects.bulk_create(mv_feature_state_values)

    @staticmethod
    def get_feature_state_key_name(fsv_type) -> str:
        return {
            INTEGER: "integer_value",
            BOOLEAN: "boolean_value",
            STRING: "string_value",
        }.get(fsv_type)

    @staticmethod
    def get_feature_state_value_type(value) -> str:
        fsv_type = type(value).__name__
        accepted_types = (STRING, INTEGER, BOOLEAN)

        # Default to string if not an anticipate type value to keep backwards compatibility.
        return fsv_type if fsv_type in accepted_types else STRING

    @classmethod
    def create_initial_feature_states_for_environment(
        cls, environment: "Environment"
    ) -> None:
        for feature in environment.project.features.all():
            cls._create_initial_feature_state(feature=feature, environment=environment)

    @classmethod
    def create_initial_feature_states_for_feature(cls, feature: "Feature") -> None:
        for environment in feature.project.environments.all():
            cls._create_initial_feature_state(feature=feature, environment=environment)

    @classmethod
    def _create_initial_feature_state(
        cls, feature: "Feature", environment: "Environment"
    ) -> None:
        kwargs = {
            "feature": feature,
            "environment": environment,
            "enabled": (
                False
                if environment.project.prevent_flag_defaults
                else feature.default_enabled
            ),
        }
        if environment.use_v2_feature_versioning:
            kwargs.update(
                environment_feature_version=EnvironmentFeatureVersion.create_initial_version(
                    environment=environment, feature=feature
                )
            )

        cls.objects.create(**kwargs)

    @classmethod
    def get_next_version_number(
        cls,
        environment_id: int,
        feature_id: int,
        feature_segment_id: int,
        identity_id: int,
    ):
        return (
            cls.objects.filter(
                environment__id=environment_id,
                feature__id=feature_id,
                feature_segment__id=feature_segment_id,
                identity__id=identity_id,
            )
            .aggregate(max_version=Max("version"))
            .get("max_version", 0)
            + 1
        )

    def is_more_recent_live_from(self, other: "FeatureState") -> bool:
        return (
            (
                self.live_from is not None
                and other.live_from is not None
                and (self.live_from > other.live_from)
            )
            or self.live_from is not None
            and other.live_from is None
        )

    @property
    def belongs_to_uncommited_change_request(self) -> bool:
        return self.change_request_id and not self.change_request.committed_at

    def get_skip_create_audit_log(self) -> bool:
        if self.belongs_to_uncommited_change_request:
            # Change requests can create, update, or delete feature states that may never go live,
            # since we already include the change requests in the audit log
            # we don't want to create separate audit logs for the associated
            # feature states
            return True
        elif self.environment_feature_version_id is not None:
            # Don't create audit logs for feature states created using versioning
            # v2 as we rely on the version history instead.
            return True

        return False

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        if (
            history_instance.history_type == "+"
            and (self.identity_id or self.feature_segment_id)
            and self.enabled == self.get_environment_default().enabled
        ):
            # Don't create an Audit Log for overrides that are created which don't differ
            # from the environment default. This likely means that an override was created
            # for a remote config value, and hence there will be an AuditLog message
            # created for the FeatureStateValue model change.
            return

        if self.identity_id:
            return audit_helpers.get_identity_override_created_audit_message(self)
        elif self.feature_segment_id:
            return audit_helpers.get_segment_override_created_audit_message(self)

        if self.environment.created_date > self.feature.created_date:
            # Don't create an audit log record for feature states created when
            # creating an environment
            return

        return audit_helpers.get_environment_feature_state_created_audit_message(self)

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        if self.identity:
            return IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (
                self.feature.name,
                self.identity.identifier,
            )
        elif self.feature_segment:
            return SEGMENT_FEATURE_STATE_UPDATED_MESSAGE % (
                self.feature.name,
                self.feature_segment.segment.name,
            )
        return FEATURE_STATE_UPDATED_MESSAGE % self.feature.name

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        try:
            if self.identity_id:
                return IDENTITY_FEATURE_STATE_DELETED_MESSAGE % (
                    self.feature.name,
                    self.identity.identifier,
                )
            elif self.feature_segment_id:
                return None  # handled by FeatureSegment

            # TODO: this is here to maintain current functionality, however, I'm not
            #  sure that we want to create an audit log record in this case
            return FEATURE_DELETED_MESSAGE % self.feature.name
        except ObjectDoesNotExist:
            # Account for cascade deletes
            return None

    def get_extra_audit_log_kwargs(self, history_instance) -> dict:
        kwargs = super().get_extra_audit_log_kwargs(history_instance)

        if (
            history_instance.history_type == "+"
            and self.feature_segment_id is None
            and self.identity_id is None
        ):
            kwargs["skip_signals_and_hooks"] = "send_environments_to_dynamodb"

        return kwargs

    def get_environment_default(self) -> typing.Optional["FeatureState"]:
        if self.feature_segment_id or self.identity_id:
            return (
                self.__class__.objects.get_live_feature_states(
                    environment=self.environment,
                    feature_id=self.feature_id,
                    feature_segment_id__isnull=True,
                    identity_id__isnull=True,
                )
                .order_by("-version", "-environment_feature_version__live_from")
                .first()
            )

        return None

    def _get_environment(self) -> typing.Optional["Environment"]:
        return self.environment

    def _get_project(self) -> typing.Optional["Project"]:
        return self.feature.project

    def _is_more_recent_version(self, other: "FeatureState") -> bool:
        return (
            self.version is not None
            and other.version is not None
            and self.version > other.version
        ) or (self.version is not None and other.version is None)

    @staticmethod
    def copy_identity_feature_states(
        target_identity: "Identity", source_identity: "Identity"
    ) -> None:
        target_feature_states: dict[int, FeatureState] = (
            target_identity.get_overridden_feature_states()
        )
        source_feature_states: dict[int, FeatureState] = (
            source_identity.get_overridden_feature_states()
        )

        # Delete own feature states not in source_identity
        feature_states_to_delete = list(
            target_feature_states.keys() - source_feature_states.keys()
        )
        for feature_state_id in feature_states_to_delete:
            target_feature_states[feature_state_id].delete()

        # Clone source_identity's feature states to target_identity
        for source_feature_id, source_feature_state in source_feature_states.items():
            # Get target feature_state if exists in target identity or create new one
            target_feature_state: FeatureState = target_feature_states.get(
                source_feature_id
            ) or FeatureState.objects.create(
                environment=target_identity.environment,
                identity=target_identity,
                feature=source_feature_state.feature,
            )

            # Copy enabled value from source feature_state
            target_feature_state.enabled = source_feature_states[
                source_feature_id
            ].enabled

            # Copy feature state value from source feature_state
            target_feature_state.feature_state_value.copy_from(
                source_feature_state.feature_state_value
            )

            # Save changes to target feature_state
            target_feature_state.save()


class FeatureStateValue(
    AbstractBaseFeatureValueModel,
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    related_object_type = RelatedObjectType.FEATURE_STATE
    history_record_class_path = "features.models.HistoricalFeatureStateValue"

    # After a FeatureState is created, a FeatureStateValue is
    # automatically created in a post create hook.
    feature_state = models.OneToOneField(
        FeatureState, related_name="feature_state_value", on_delete=models.CASCADE
    )

    objects = FeatureStateValueManager()

    def clone(self, feature_state: FeatureState) -> "FeatureStateValue":
        clone = deepcopy(self)
        clone.id = None
        clone.uuid = uuid.uuid4()
        clone.feature_state = feature_state
        clone.save()
        return clone

    def copy_from(self, source_feature_state_value: "FeatureStateValue"):
        # Copy feature state type and values from given feature state value.
        self.type = source_feature_state_value.type
        self.boolean_value = source_feature_state_value.boolean_value
        self.integer_value = source_feature_state_value.integer_value
        self.string_value = source_feature_state_value.string_value
        self.save()

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        fs = self.feature_state

        changes = history_instance.diff_against(history_instance.prev_record).changes
        if (
            len(changes) == 1
            and changes[0].field == "string_value"
            and changes[0].old in (None, "")
            and changes[0].new in (None, "")
        ):
            # When we create a new segment override, for some reason, there are changes made to the
            # existing segment overrides which change the string value between null and empty string
            # since this change has no significant impact on the platform, we simply check for it here
            # and ignore it.
            return

        if fs.change_request_id and not fs.change_request.committed_at:
            return

        feature = fs.feature

        if fs.identity_id:
            return IDENTITY_FEATURE_STATE_VALUE_UPDATED_MESSAGE % (
                feature.name,
                fs.identity.identifier,
            )
        elif fs.feature_segment_id:
            segment = fs.feature_segment.segment
            return SEGMENT_FEATURE_STATE_VALUE_UPDATED_MESSAGE % (
                feature.name,
                segment.name,
            )

        return FEATURE_STATE_VALUE_UPDATED_MESSAGE % feature.name

    def _get_environment(self) -> typing.Optional["Environment"]:
        return self.feature_state.environment
