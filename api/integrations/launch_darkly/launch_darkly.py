from typing import Optional
from uuid import UUID

from django.db import IntegrityError

from environments.models import Environment
from features.feature_types import STANDARD
from features.models import Feature, FeatureState, FeatureStateValue
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.value_types import BOOLEAN, FLOAT, INTEGER, STRING
from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.serializers import LaunchDarklyImportSerializer
from organisations.models import Organisation
from projects.models import Project


class LaunchDarklyWrapper:
    def __init__(self, api_key: str):
        self.client = LaunchDarklyClient(api_key)

    def import_data(self, request: LaunchDarklyImportSerializer):
        organisation = Organisation.objects.get(pk=request["organisation_id"])

        try:
            project_id = request["project_id"]
            project = Project.objects.get(project_id)
        except KeyError:
            ld_project = self.client.get_project(request["ld_project_id"])
            project = self._create_project(organisation, ld_project)

        ld_environments = self.client.get_environments(request["ld_project_id"])
        ld_flags = self.client.get_flags(request["ld_project_id"])

        environments = []
        for ld_environment in ld_environments:
            environment = self._create_environment(ld_environment, project)
            environments.append(environment)

        for ld_flag in ld_flags:
            feature = self._create_feature(ld_flag, environments)

    def _create_project(self, organisation_id: UUID, ld_project: dict) -> Project:
        return Project.objects.create(
            organisation_id=organisation_id, name=ld_project.get("name")
        )

    def _create_environment(self, ld_environment, project: Project) -> Environment:
        return Environment.objects.create(
            name=ld_environment.get("name"),
            project=project,
        )

    def _create_feature(
        self, ld_flag, environments: list[Environment], project: Project
    ):
        match ld_flag.get("kind"):
            case "boolean":
                self._create_boolean_feature(ld_flag, environments, project)
            case "multivariate":
                self._create_multivariate_feature(ld_flag, environments, project)
            case _:
                raise Exception("Invalid flag type from Launch Darkly")

    def _create_boolean_feature(
        self, ld_flag, environments: list[Environment], project: Project
    ):
        # todo try get tags
        try:
            feature = Feature.objects.create(
                name=ld_flag.get("key"),
                project=project,
                initial_value=None,  # todo
                description=ld_flag.get("description"),
                default_enabled=None,  # todo
                type=STANDARD,
                tags=None,  # todo
                is_archived=ld_flag.get("archived", False),
                owners=None,  # todo
                is_server_key_only=None,  # todo
            )
        except IntegrityError:
            # Feature with this name already exists
            # todo do we want to update or just log and ignore this one?
            pass

        for environment in environments:
            ld_environment = ld_flag.get("environments", {}).get(environment.name)
            if ld_environment:
                feature_state = FeatureState.objects.create(
                    feature=feature,
                    environment=environment,
                    identity=None,  # todo
                    feature_segment=None,  # todo
                    enabled=ld_environment.get("_summary").get("on"),
                )
                FeatureStateValue.objects.create(feature_state=feature_state)

    def _create_multivariate_feature(
        self, ld_flag, environments: list[Environment], project: Project
    ):
        # todo try get tags
        try:
            feature = Feature.objects.create(
                name=ld_flag.get("key"),
                project=project,
                initial_value=None,  # todo
                description=ld_flag.get("description"),
                default_enabled=None,  # todo
                type=STANDARD,
                tags=None,  # todo
                is_archived=ld_flag.get("archived", False),
                owners=None,  # todo
                is_server_key_only=None,  # todo
            )
        except IntegrityError:
            # Feature with this name already exists
            # todo do we want to update or just log and ignore this one?
            pass
        feature_options = {}
        for variant in ld_flag.get("variations"):
            value = variant.get("value")
            variant_type = self._get_multivariant_kind(value)
            variant_values = self._get_multivariant_value(value, variant_type)
            feature_option = MultivariateFeatureOption.objects.create(
                feature=feature,
                type=variant_type,
                boolean_value=variant_values[0],
                integer_value=variant_values[1],
                string_value=variant_values[2],
            )
            feature_options[value] = feature_option

        for environment in environments:
            ld_environment = ld_flag.get("environments", {}).get(environment.name)
            if ld_environment:
                env_feature_option = feature_options.get(ld_environment.get(""))
                MultivariateFeatureStateValue.objects.create(
                    feature=feature,
                    environment=environment,
                    identity=None,  # todo
                    feature_segment=None,  # todo
                    enabled=ld_environment.get("_summary").get("on"),
                    multivariate_feature_option=env_feature_option,
                    updated_at=ld_environment.get("_summary").get("lastModified"),
                )

    def _get_multivariant_kind(self, value: any) -> str:
        if isinstance(value, bool):
            return BOOLEAN
        if isinstance(value, str):
            return STRING
        if isinstance(value, float):
            return FLOAT
        if isinstance(value, int):
            return INTEGER
        return STRING

    def _get_multivariant_value(
        self, value: any, type: str
    ) -> (Optional[bool], Optional[int], Optional[str]):
        if type == BOOLEAN:
            return (value, None, None)
        if type in [INTEGER, FLOAT]:
            return (None, int(value), None)
        if type == STRING:
            return (None, None, value)
        raise Exception()
