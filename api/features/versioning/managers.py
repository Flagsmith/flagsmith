import typing
from pathlib import Path

from django.db.models import QuerySet
from softdelete.models import SoftDeleteManager

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.versioning.models import EnvironmentFeatureVersion


with open(Path(__file__).parent.resolve() / "sql/get_latest_versions.sql") as f:
    get_latest_version_uuids_for_environment = f.read()


class EnvironmentFeatureVersionManager(SoftDeleteManager):
    def get_latest_version_uuids(
        self, environment: "Environment"
    ) -> QuerySet["EnvironmentFeatureVersion"]:
        return self.raw(
            get_latest_version_uuids_for_environment,
            params={"environment_id": environment.id},
        )
