import logging
import typing
import uuid
from copy import deepcopy
from typing import TYPE_CHECKING, Literal

from common.core.utils import using_database_replica
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.cache import caches
from django.db import models
from django.db.models import Max, Prefetch, Q, QuerySet
from django.utils import timezone
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    AFTER_DELETE,
    AFTER_SAVE,
    AFTER_UPDATE,
    BEFORE_SAVE,
    LifecycleModel,
    hook,
)
from rest_framework.request import Request
from softdelete.models import SoftDeleteObject  # type: ignore[import-untyped]

from app.utils import create_hash
from audit.constants import (
    ENVIRONMENT_CREATED_MESSAGE,
    ENVIRONMENT_UPDATED_MESSAGE,
)
from audit.related_object_type import RelatedObjectType
from core.models import abstract_base_auditable_model_factory
from core.request_origin import RequestOrigin
from environments.api_keys import (
    generate_client_api_key,
    generate_server_api_key,
)
from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from environments.dynamodb import (
    DynamoEnvironmentAPIKeyWrapper,
    DynamoEnvironmentV2Wrapper,
    DynamoEnvironmentWrapper,
)
from environments.enums import EnvironmentDocumentCacheMode
from environments.exceptions import EnvironmentHeaderNotPresentError
from environments.managers import EnvironmentManager
from environments.metrics import (
    CACHE_HIT,
    CACHE_MISS,
    flagsmith_environment_document_cache_queries_total,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from integrations.flagsmith.client import get_client
from metadata.models import Metadata
from projects.models import Project
from segments.models import Segment
from util.mappers import (
    map_environment_to_environment_document,
    map_environment_to_sdk_document,
)
from webhooks.models import AbstractBaseExportableWebhookModel

if TYPE_CHECKING:
    from features.workflows.core.models import ChangeRequest


logger = logging.getLogger(__name__)

environment_cache = caches[settings.ENVIRONMENT_CACHE_NAME]
environment_document_cache = caches[settings.CACHE_ENVIRONMENT_DOCUMENT_LOCATION]
environment_segments_cache = caches[settings.ENVIRONMENT_SEGMENTS_CACHE_NAME]
bad_environments_cache = caches[settings.BAD_ENVIRONMENTS_CACHE_LOCATION]

# Intialize the dynamo environment wrapper(s) globaly
environment_wrapper = DynamoEnvironmentWrapper()
environment_v2_wrapper = DynamoEnvironmentV2Wrapper()
environment_api_key_wrapper = DynamoEnvironmentAPIKeyWrapper()


class Environment(
    LifecycleModel,  # type: ignore[misc]
    abstract_base_auditable_model_factory(  # type: ignore[misc]
        change_details_excluded_fields=["updated_at"],
        historical_records_excluded_fields=["uuid"],
    ),
    SoftDeleteObject,  # type: ignore[misc]
):
    history_record_class_path = "environments.models.HistoricalEnvironment"
    related_object_type = RelatedObjectType.ENVIRONMENT

    name = models.CharField(max_length=2000)  # type: ignore[var-annotated]
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)  # type: ignore[var-annotated]
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)  # type: ignore[var-annotated]
    description = models.TextField(null=True, blank=True, max_length=20000)  # type: ignore[var-annotated]
    project = models.ForeignKey(  # type: ignore[var-annotated]
        "projects.Project",
        related_name="environments",
        help_text=(
            "Changing the project selected will remove all previous Feature States for"
            " the previously associated projects Features that are related to this"
            " Environment. New default Feature States will be created for the new"
            " selected projects Features for this Environment."
        ),
        # Cascade deletes are decouple from the Django ORM. See this PR for details.
        # https://github.com/Flagsmith/flagsmith/pull/3360/
        on_delete=models.DO_NOTHING,
    )

    api_key = models.CharField(  # type: ignore[var-annotated]
        default=generate_client_api_key, unique=True, max_length=100
    )

    minimum_change_request_approvals = models.IntegerField(blank=True, null=True)  # type: ignore[var-annotated]

    webhooks_enabled = models.BooleanField(default=False, help_text="DEPRECATED FIELD.")  # type: ignore[var-annotated]  # noqa: E501
    webhook_url = models.URLField(null=True, blank=True, help_text="DEPRECATED FIELD.")  # type: ignore[var-annotated]

    allow_client_traits = models.BooleanField(  # type: ignore[var-annotated]
        default=True, help_text="Allows clients using the client API key to set traits."
    )
    updated_at = models.DateTimeField(  # type: ignore[var-annotated]
        default=timezone.now,
        help_text="Tracks changes to self and related entities, e.g. FeatureStates.",
    )
    banner_text = models.CharField(null=True, blank=True, max_length=255)  # type: ignore[var-annotated]
    banner_colour = models.CharField(  # type: ignore[var-annotated]
        null=True, blank=True, max_length=7, help_text="hex code for the banner colour"
    )
    metadata = GenericRelation(Metadata)

    hide_disabled_flags = models.BooleanField(  # type: ignore[var-annotated]
        null=True,
        blank=True,
        help_text=(
            "If true will exclude flags from SDK which are disabled. NOTE: If set, this"
            " will override the project `hide_disabled_flags`"
        ),
    )
    use_identity_composite_key_for_hashing = models.BooleanField(  # type: ignore[var-annotated]
        default=True,
        help_text=(
            "Enable this to have consistent multivariate and percentage split evaluations "
            "across all SDKs (in local and server side mode)"
        ),
        db_column="use_mv_v2_evaluation",  # see https://github.com/Flagsmith/flagsmith/issues/2186
    )
    hide_sensitive_data = models.BooleanField(  # type: ignore[var-annotated]
        default=False,
        help_text="If true, will hide sensitive data(e.g: traits, description etc) from the SDK endpoints",
    )

    use_v2_feature_versioning = models.BooleanField(default=False)  # type: ignore[var-annotated]
    use_identity_overrides_in_local_eval = models.BooleanField(  # type: ignore[var-annotated]
        default=True,
        help_text="When enabled, identity overrides will be included in the environment document",
    )

    is_creating = models.BooleanField(  # type: ignore[var-annotated]
        default=False,
        help_text="Attribute used to indicate when an environment is still being created (via clone for example)",
    )

    objects = EnvironmentManager()

    class Meta:
        ordering = ["id"]

    @hook(AFTER_CREATE)  # type: ignore[misc]
    def create_feature_states(self) -> None:
        FeatureState.create_initial_feature_states_for_environment(environment=self)

    @hook(AFTER_UPDATE)  # type: ignore[misc]
    def clear_environment_cache(self) -> None:
        # TODO: this could rebuild the cache itself (using an async task)
        environment_cache.delete_many(
            [self.initial_value("api_key"), *[eak.key for eak in self.api_keys.all()]]
        )

    @hook(AFTER_UPDATE, when="api_key", has_changed=True)  # type: ignore[misc]
    def update_environment_document_cache(self) -> None:
        environment_document_cache.delete(self.initial_value("api_key"))
        self.write_environment_documents(self.id)

    @hook(AFTER_DELETE)  # type: ignore[misc]
    def delete_from_dynamo(self) -> None:
        if self.project.enable_dynamo_db and environment_wrapper.is_enabled:
            from environments.tasks import delete_environment_from_dynamo

            delete_environment_from_dynamo.delay(args=(self.api_key, self.id))

    @hook(AFTER_DELETE)  # type: ignore[misc]
    def delete_environment_document_from_cache(self) -> None:
        if (
            settings.CACHE_ENVIRONMENT_DOCUMENT_MODE
            == EnvironmentDocumentCacheMode.PERSISTENT
            or settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS > 0
        ):
            environment_document_cache.delete(self.api_key)

    # Use the BEFORE_SAVE hook instead of BEFORE_CREATE to account for the logic in the
    # Environment.clone() method
    @hook(BEFORE_SAVE, when="pk", is_now=None)  # type: ignore[misc]
    def enable_v2_versioning(self) -> None:
        if self.use_v2_feature_versioning:
            # if the environment has already been created with versioning enabled,
            # we don't want to disable it based on the flag state.
            return

        flagsmith_client = get_client("local", local_eval=True)
        organisation = self.project.organisation
        enable_v2_versioning = flagsmith_client.get_identity_flags(
            organisation.flagsmith_identifier,
            traits=organisation.flagsmith_on_flagsmith_api_traits,
        ).is_feature_enabled("enable_feature_versioning_for_new_environments")
        self.use_v2_feature_versioning = enable_v2_versioning

    def __str__(self):  # type: ignore[no-untyped-def]
        return "Project %s - Environment %s" % (self.project.name, self.name)

    def natural_key(self):  # type: ignore[no-untyped-def]
        return (self.api_key,)

    @property
    def is_workflow_enabled(self) -> bool:
        return self.minimum_change_request_approvals is not None

    def clone(
        self,
        name: str,
        api_key: str = None,  # type: ignore[assignment]
        clone_feature_states_async: bool = False,
    ) -> "Environment":
        """
        Creates a clone of the environment, related objects and returns the
        cloned object after saving it to the database.
        # NOTE: clone will not trigger create hooks
        """
        clone = deepcopy(self)
        clone.id = None
        clone.uuid = uuid.uuid4()
        clone.name = name
        clone.api_key = api_key if api_key else create_hash()
        clone.is_creating = True
        clone.save()

        from environments.tasks import clone_environment_feature_states

        kwargs = {"source_environment_id": self.id, "clone_environment_id": clone.id}

        if clone_feature_states_async:
            clone_environment_feature_states.delay(kwargs=kwargs)
        else:
            clone_environment_feature_states(**kwargs)

        return clone

    @staticmethod
    def get_environment_from_request(request):  # type: ignore[no-untyped-def]
        try:
            environment_key = request.META["HTTP_X_ENVIRONMENT_KEY"]
        except KeyError:
            raise EnvironmentHeaderNotPresentError

        return Environment.objects.select_related(
            "project", "project__organisation"
        ).get(api_key=environment_key)

    @classmethod
    def get_from_cache(cls, api_key: str | None) -> "Environment | None":
        if not api_key:
            logger.warning("Requested environment with null api_key.")
            return None

        if cls.is_bad_key(api_key):
            return None

        environment: "Environment" = environment_cache.get(api_key)
        if not environment:
            select_related_args = (
                "project",
                "project__organisation",
                *IDENTITY_INTEGRATIONS_RELATION_NAMES,
            )
            base_qs = cls.objects.select_related(*select_related_args).defer(
                "description"
            )
            qs_for_embedded_api_key = base_qs.filter(api_key=api_key)
            qs_for_fk_api_key = base_qs.filter(api_keys__key=api_key)

            try:
                environment = qs_for_embedded_api_key.union(qs_for_fk_api_key).get()
            except cls.DoesNotExist:
                cls.set_bad_key(api_key)
                logger.info("Environment with api_key %s does not exist" % api_key)
                return None
            else:
                environment_cache.set(
                    api_key,
                    environment,
                    timeout=settings.ENVIRONMENT_CACHE_SECONDS,
                )

        return environment

    @classmethod
    def write_environment_documents(
        cls,
        environment_id: int = None,  # type: ignore[assignment]
        project_id: int = None,  # type: ignore[assignment]
    ) -> None:
        # use a list to make sure the entire qs is evaluated up front
        environments_filter = (
            Q(id=environment_id) if environment_id else Q(project_id=project_id)
        )
        environments = list(
            cls.objects.filter_for_document_builder(
                environments_filter,
                extra_select_related=IDENTITY_INTEGRATIONS_RELATION_NAMES,
                extra_prefetch_related=[
                    Prefetch(
                        "feature_states",
                        queryset=FeatureState.objects.select_related(
                            "feature", "feature_state_value"
                        ),
                    ),
                    Prefetch(
                        "feature_states__multivariate_feature_state_values",
                        queryset=MultivariateFeatureStateValue.objects.select_related(
                            "multivariate_feature_option"
                        ),
                    ),
                ],
            )
        )
        if not environments:
            return

        # grab the first project and verify that each environment is for the same
        # project (which should always be the case). Since we're working with fairly
        # small querysets here, this shouldn't have a noticeable impact on performance.
        project: Project | None = getattr(environments[0], "project", None)
        if project is None:  # pragma: no cover
            return

        for environment in environments[1:]:
            if not environment.project == project:  # pragma: no cover
                raise RuntimeError("Environments must all belong to the same project.")

        if project.enable_dynamo_db and environment_wrapper.is_enabled:
            environment_wrapper.write_environments(environments)

            if (
                project.edge_v2_environments_migrated
                and environment_v2_wrapper.is_enabled
            ):
                environment_v2_wrapper.write_environments(environments)
        elif (
            settings.CACHE_ENVIRONMENT_DOCUMENT_MODE
            == EnvironmentDocumentCacheMode.PERSISTENT
        ):
            environment_document_cache.set_many(
                {
                    e.api_key: map_environment_to_environment_document(e)
                    for e in environments
                }
            )

    def get_feature_state(
        self,
        feature_id: int,
        filter_kwargs: dict = None,  # type: ignore[type-arg,assignment]
    ) -> typing.Optional[FeatureState]:
        """
        Get the corresponding feature state in an environment for a given feature id.
        Optionally override the kwargs passed to filter to get the feature state for
        a feature segment or identity.
        """

        if not filter_kwargs:
            filter_kwargs = {"feature_segment_id": None, "identity_id": None}

        return next(  # type: ignore[no-any-return]
            filter(
                lambda fs: fs.feature.id == feature_id,
                self.feature_states.filter(**filter_kwargs),
            )
        )

    def get_identity_overrides_queryset(self) -> QuerySet[FeatureState]:
        ids = self._get_active_feature_states_ids(
            "identity_id",
            {"identity__isnull": False, "feature_segment__isnull": True},
        )
        result: QuerySet[FeatureState] = FeatureState.objects.filter(id__in=ids)
        return result

    def _get_active_feature_states_ids(
        self,
        extra_group_by_fields: Literal["identity_id"] | None = None,
        filter_kwargs: dict[str, typing.Any] | None = None,
    ) -> list[int]:
        base_qs = FeatureState.objects.get_live_feature_states(
            environment=self,
            **(filter_kwargs or {}),
        ).filter(
            feature__is_archived=False,
        )

        group_fields = ["feature_id", "environment_id"]
        if extra_group_by_fields is not None:
            group_fields.append(extra_group_by_fields)

        return list(
            base_qs.values(*group_fields)
            .annotate(id=Max("id"))
            .values_list("id", flat=True)
        )

    def get_features_metrics_queryset(self) -> QuerySet[FeatureState]:
        ids = self._get_active_feature_states_ids(
            None,
            {"identity__isnull": True, "feature_segment__isnull": True},
        )
        result: QuerySet[FeatureState] = FeatureState.objects.filter(id__in=ids)
        return result

    def _get_latest_segment_state_ids_subquery(self) -> list[int]:
        feature_states_qs = FeatureState.objects.get_live_feature_states(
            environment=self,
            additional_filters=Q(
                identity_id__isnull=True,
                feature_segment_id__isnull=False,
            ),
        ).filter(feature__is_archived=False)

        return list(
            feature_states_qs.values(
                "feature_id", "feature_segment_id", "environment_id"
            )
            .annotate(id=Max("id"))
            .values_list("id", flat=True)
        )

    def get_segment_metrics_queryset(self) -> QuerySet[FeatureState]:
        ids = self._get_latest_segment_state_ids_subquery()
        result: QuerySet[FeatureState] = FeatureState.objects.filter(id__in=ids)
        return result

    def get_change_requests_metrics_queryset(self) -> QuerySet["ChangeRequest"]:
        from features.workflows.core.models import ChangeRequest

        result: QuerySet["ChangeRequest"] = ChangeRequest.objects.filter(
            environment=self,
            committed_at__isnull=True,
            deleted_at__isnull=True,
        )
        return result

    def get_scheduled_metrics_queryset(self) -> QuerySet[FeatureState]:
        from features.workflows.core.models import ChangeRequest

        qs = ChangeRequest.objects.filter(
            environment=self,
            committed_at__isnull=False,
            deleted_at__isnull=True,
        )
        scheduled_q = (
            Q(
                Q(feature_states__deleted_at__isnull=True)
                & Q(feature_states__live_from__gt=timezone.now())
            )
            | Q(
                Q(environment_feature_versions__deleted_at__isnull=True)
                & Q(environment_feature_versions__live_from__gt=timezone.now())
            )
            | Q(
                Q(change_sets__deleted_at__isnull=True)
                & Q(change_sets__live_from__gt=timezone.now())
            )
        )
        ids = qs.filter(scheduled_q).values_list("id", flat=True)
        unique_ids = list(set(ids))
        change_requests_qs: QuerySet["ChangeRequest"] = ChangeRequest.objects.filter(
            id__in=unique_ids
        )
        return change_requests_qs

    @staticmethod
    def is_bad_key(environment_key: str) -> bool:
        return (
            settings.CACHE_BAD_ENVIRONMENTS_SECONDS > 0
            and bad_environments_cache.get(environment_key, 0)
            >= settings.CACHE_BAD_ENVIRONMENTS_AFTER_FAILURES
        )

    @staticmethod
    def set_bad_key(environment_key: str) -> None:
        if settings.CACHE_BAD_ENVIRONMENTS_SECONDS:
            current_count = bad_environments_cache.get(environment_key, 0)
            bad_environments_cache.set(
                environment_key,
                current_count + 1,
                timeout=settings.CACHE_BAD_ENVIRONMENTS_SECONDS,
            )

    def trait_persistence_allowed(self, request: Request) -> bool:
        return (
            self.allow_client_traits
            or getattr(request, "originated_from", RequestOrigin.CLIENT)
            == RequestOrigin.SERVER
        )

    def get_segments_from_cache(self) -> typing.List[Segment]:
        """
        Get any segments that have been overridden in this environment.
        """
        segments = environment_segments_cache.get(self.id)
        if not segments:
            segments = list(
                Segment.live_objects.filter(
                    feature_segments__feature_states__environment=self
                ).prefetch_related(
                    "rules",
                    "rules__conditions",
                    "rules__rules",
                    "rules__rules__conditions",
                    "rules__rules__rules",
                )
            )
            environment_segments_cache.set(self.id, segments)
        return segments  # type: ignore[no-any-return]

    @classmethod
    def get_environment_document(
        cls,
        api_key: str,
    ) -> dict[str, typing.Any]:
        if (
            settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS > 0
            or settings.CACHE_ENVIRONMENT_DOCUMENT_MODE
            == EnvironmentDocumentCacheMode.PERSISTENT
        ):
            return cls._get_environment_document_from_cache(api_key)
        return cls._get_environment_document_from_db(api_key)

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        return ENVIRONMENT_CREATED_MESSAGE % self.name  # type: ignore[no-any-return]

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:  # type: ignore[no-untyped-def]
        return ENVIRONMENT_UPDATED_MESSAGE % self.name  # type: ignore[no-any-return]

    def get_hide_disabled_flags(self) -> bool:
        if self.hide_disabled_flags is not None:
            return self.hide_disabled_flags  # type: ignore[no-any-return]

        return self.project.hide_disabled_flags  # type: ignore[no-any-return]

    @classmethod
    def _get_environment_document_from_cache(
        cls,
        api_key: str,
    ) -> dict[str, typing.Any]:
        environment_document = environment_document_cache.get(api_key)
        if not (cache_hit := environment_document is not None):
            environment_document = cls._get_environment_document_from_db(api_key)
            environment_document_cache.set(api_key, environment_document)

        flagsmith_environment_document_cache_queries_total.labels(
            result=CACHE_HIT if cache_hit else CACHE_MISS,
        ).inc()

        return environment_document  # type: ignore[no-any-return]

    @classmethod
    def _get_environment_document_from_db(
        cls,
        api_key: str,
    ) -> dict[str, typing.Any]:
        manager = using_database_replica(cls.objects)
        environment = manager.filter_for_document_builder(
            api_key=api_key,
            extra_prefetch_related=[
                Prefetch(
                    "feature_states",
                    queryset=FeatureState.objects.select_related(
                        "feature",
                        "feature_state_value",
                        "identity",
                        "environment_feature_version",
                        "identity__environment",
                    ).prefetch_related(
                        Prefetch(
                            "identity__identity_features",
                            queryset=FeatureState.objects.select_related(
                                "feature", "feature_state_value", "environment"
                            ),
                        ),
                        Prefetch(
                            "identity__identity_features__multivariate_feature_state_values",
                            queryset=MultivariateFeatureStateValue.objects.select_related(
                                "multivariate_feature_option"
                            ),
                        ),
                    ),
                ),
                Prefetch(
                    "feature_states__multivariate_feature_state_values",
                    queryset=MultivariateFeatureStateValue.objects.select_related(
                        "multivariate_feature_option"
                    ),
                ),
            ],
        ).get()
        return map_environment_to_sdk_document(environment)

    def _get_environment(self):  # type: ignore[no-untyped-def]
        return self

    def _get_project(self):  # type: ignore[no-untyped-def]
        return self.project


class Webhook(AbstractBaseExportableWebhookModel):
    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_name="webhooks"
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_webhook_feature_state_data(
        feature: Feature,
        environment: Environment,
        enabled: bool,
        value: typing.Union[str, int, bool, type(None)],  # type: ignore[valid-type]
        identity_id: typing.Union[int, str] = None,  # type: ignore[assignment]
        identity_identifier: str = None,  # type: ignore[assignment]
        feature_segment: FeatureSegment = None,  # type: ignore[assignment]
    ) -> dict:  # type: ignore[type-arg]
        if (identity_id or identity_identifier) and not (
            identity_id and identity_identifier
        ):
            raise ValueError("Must provide both identity_id and identity_identifier.")

        if (identity_id and identity_identifier) and feature_segment:
            raise ValueError("Cannot provide identity information and feature segment")

        # TODO: refactor to use a serializer / schema
        data = {
            "feature": {
                "id": feature.id,
                "created_date": feature.created_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "default_enabled": feature.default_enabled,
                "description": feature.description,
                "initial_value": feature.initial_value,
                "name": feature.name,
                "project": {
                    "id": feature.project_id,
                    "name": feature.project.name,
                },
                "type": feature.type,
            },
            "environment": {
                "id": environment.id,
                "name": environment.name,
            },
            "identity": identity_id,
            "identity_identifier": identity_identifier,
            "feature_segment": None,
            "enabled": enabled,
            "feature_state_value": value,
        }
        if feature_segment:
            data["feature_segment"] = {
                "segment": {
                    "id": feature_segment.segment_id,
                    "name": feature_segment.segment.name,
                    "description": feature_segment.segment.description,
                },
                "priority": feature_segment.priority,
            }
        return data


class EnvironmentAPIKey(LifecycleModel):  # type: ignore[misc]
    """
    These API keys are only currently used for server side integrations.
    """

    environment = models.ForeignKey(  # type: ignore[var-annotated]
        Environment, on_delete=models.CASCADE, related_name="api_keys"
    )
    key = models.CharField(default=generate_server_api_key, max_length=100, unique=True)  # type: ignore[var-annotated]  # noqa: E501
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore[var-annotated]
    name = models.CharField(max_length=100)  # type: ignore[var-annotated]
    expires_at = models.DateTimeField(blank=True, null=True)  # type: ignore[var-annotated]
    active = models.BooleanField(default=True)  # type: ignore[var-annotated]

    def natural_key(self):  # type: ignore[no-untyped-def]
        return (self.key,)

    @property
    def is_valid(self) -> bool:
        return self.active and (not self.expires_at or self.expires_at > timezone.now())

    @hook(AFTER_SAVE, when="_should_update_dynamo", is_now=True)
    def send_to_dynamo(self):  # type: ignore[no-untyped-def]
        environment_api_key_wrapper.write_api_key(self)

    @hook(AFTER_DELETE, when="_should_update_dynamo", is_now=True)
    def delete_from_dynamo(self):  # type: ignore[no-untyped-def]
        environment_api_key_wrapper.delete_api_key(self.key)

    @property
    def _should_update_dynamo(self) -> bool:
        return (
            self.environment.project.enable_dynamo_db
            and environment_api_key_wrapper.is_enabled
        )
