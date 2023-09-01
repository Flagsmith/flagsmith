import logging
from datetime import datetime
from typing import Optional

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
from integrations.launch_darkly.models import LaunchDarklyImport
from integrations.launch_darkly.serializers import LaunchDarklyImportSerializer
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


logger = logging.getLogger(__name__)


class LaunchDarklyWrapper:
    def __init__(
        self,
        user: FFAdminUser,
        request: LaunchDarklyImportSerializer,
        client: LaunchDarklyClient = None,
    ):
        request.is_valid(raise_exception=True)
        self.request = request.validated_data
        self.client = client or LaunchDarklyClient(self.request["api_key"])
        self.logger = LaunchDarklyImport.objects.create(
            created_by=user,
            organisation_id=self.request["organisation_id"],
            project=self.request["project_id"],
        )
        self.import_id = self.logger.uuid

    def import_data(self) -> LaunchDarklyImport:
        self.logger.info(
            f"Starting Launch Darkly feature importer for job id: {self.import_id}"
        )
        organisation_id = self.request["organisation_id"]
        self.logger.info(
            f"Attempting to retrieve Flagsmith organisation with id: {organisation_id}"
        )
        try:
            organisation = Organisation.objects.get(pk=organisation_id)
            self.logger.info(
                f"Successfully retrieved Flagsmith organisation with id: {organisation_id}"
            )
        except Organisation.DoesNotExist:
            self.logger.critical(
                f"Could not find Flagsmith organisation with id: {organisation_id}"
            )
            # Todo kill import here
            raise Exception()

        ld_project_id = self.request["ld_project_id"]
        try:
            project_id = self.request["project_id"]
            self.logger.info(
                f"Attempting to retrieve Flagsmith project with id: {project_id}"
            )
            project = Project.objects.get(pk=project_id)
            self.logger.info(
                f"Successfully retrieved Flagsmith project with id: {project_id}"
            )
        except (KeyError, Project.DoesNotExist):
            self.logger.warning(
                f"Could not find Flagsmith project with id: {project_id}"
            )
            self.logger.info(
                "Creating new Flagsmith project for Launch Darkly's imported features"
            )
            ld_project = self.client.get_project(ld_project_id)
            project = self._create_project(organisation.id, ld_project)
            self.logger.info(
                "Successfully created new Flagsmith project for Launch Darkly's imported features"
            )

        self.logger.info(
            f"Attempting to retrieve Launch Darkly environments under project id: {ld_project_id}"
        )
        ld_environments = self.client.get_environments(ld_project_id)
        if not ld_environments:
            # todo do we want to stop the script if no environments can be found
            self.logger.warning(
                f"No environments found in Launch Darkly for project id: {ld_project_id}"
            )

        self.logger.info(
            f"Attempting to retrieve Launch Darkly flags under project id: {ld_project_id}"
        )
        ld_flags = self.client.get_flags(ld_project_id)
        if not ld_flags:
            # todo do we want to stop the script if no flags can be found
            self.logger.warning(
                f"No flags found in Launch Darkly for project id: {ld_project_id}"
            )

        environments = []
        self.logger.info(f"Adding {len(ld_environments)} environments")
        for ld_environment in ld_environments:
            environment = self._create_environment(ld_environment, project)
            environments.append(environment)

        self.logger.info(f"Adding {len(ld_flags)} features")
        for ld_flag in ld_flags:
            self._create_feature(ld_flag, environments, project)
        self.logger.completed_at = datetime.now()
        self.logger.save()

        self.logger.info("Finished importing")
        return self.logger

    def _create_project(self, organisation_id: int, ld_project: dict) -> Project:
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
                raise ("Invalid flag type from Launch Darkly")

    def _create_boolean_feature(
        self, ld_flag, environments: list[Environment], project: Project
    ):
        # todo try get tags
        try:
            feature = Feature.objects.create(
                name=ld_flag.get("key"),
                project=project,
                description=ld_flag.get("description"),
                default_enabled=False,  # default to false and set per environment based on LD values
                type=STANDARD,
                # tags=None,  # todo
                is_archived=ld_flag.get("archived", False),
                # owners=None,  # todo
            )

            for environment in environments:
                # todo: this won't work for all cases, we need the env key from ld not name
                env_name = environment.name.lower()
                ld_environment = ld_flag.get("environments", {}).get(env_name)
                if ld_environment:
                    feature_state, created = FeatureState.objects.update_or_create(
                        feature=feature,
                        environment=environment,
                        defaults={
                            "enabled": ld_environment.get("on")
                        }
                    )
                    FeatureStateValue.objects.update_or_create(feature_state=feature_state, defaults={
                        "feature_state": feature_state
                    })
                else:
                    self.logger.error(
                        f"""
                        There was a problem adding a feature state to
                         environment: {environment.name},
                         for feature: {feature.name}
                        """
                    )
        except IntegrityError as ie:
            logger.error(str(ie))
            self.logger.error(
                f"Unable to create feature with name: {ld_flag.get('key')}"
            )
        except ValueError as ve:
            logger.error(str(ve))
            self.logger.error(
                f"Unable to create feature with name: {ld_flag.get('key')}"
            )
        except Exception as e:
            logger.error(str(e))
            self.logger.error(
                f"Unable to create feature with name: {ld_flag.get('key')}"
            )

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
                type=STANDARD,
                is_archived=ld_flag.get("archived", False),
            )

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
                # todo: this won't work for all cases, we need the env key from ld not name
                env_name = environment.name.lower()
                ld_environment = ld_flag.get("environments", {}).get(env_name)
                if ld_environment:
                    env_feature_options = ld_environment.get("_summary", {}).get("variations", [])
                    for env_feature_key in env_feature_options.keys():
                        feature_state, created = FeatureState.objects.update_or_create(
                            feature=feature,
                            environment=environment,
                            defaults={
                                "enabled": ld_environment.get("on")
                            }
                        )
                        flag_value = ld_flag.get("variations", {})[int(env_feature_key)].get("value")
                        env_feature_option = feature_options.get(flag_value)
                        is_on = not env_feature_options.get(env_feature_key).get("isOff", False)
                        percentage_allocation = 100 if is_on else 0
                        MultivariateFeatureStateValue.objects.update_or_create(
                            feature_state=feature_state,
                            multivariate_feature_option=env_feature_option,
                            defaults={
                                "percentage_allocation": percentage_allocation
                            }
                        )
                        self.logger.info("Successfully ")
                else:
                    self.logger.error(
                        f"""
                        There was a problem adding a multi variant feature state to
                         environment: {environment.name},
                         for feature: {feature.name}
                        """
                    )

        except IntegrityError as ie:
            logger.error(str(ie))
            self.logger.error(
                f"Unable to create feature with name: {ld_flag.get('key')}"
            )
        except ValueError as ve:
            logger.error(str(ve))
            self.logger.error(
                f"Unable to create feature with name: {ld_flag.get('key')}"
            )
        except Exception as e:
            logger.error(str(e))
            self.logger.error(
                f"Unable to create feature with name: {ld_flag.get('key')}"
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
        if type == INTEGER:
            return (None, value, None)
        if type == FLOAT:
            self.logger.warning(
                f"Flag value:{value}, is being cast from a float to an int, some data may be lost"
            )
            return (None, int(value), None)
        if type == STRING:
            return (None, None, value)

        raise Exception()
