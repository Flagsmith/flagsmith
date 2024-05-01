import typing
from pathlib import Path

from django.db.models.query import RawQuerySet
from softdelete.models import SoftDeleteManager

if typing.TYPE_CHECKING:
    from environments.models import Environment


with open(Path(__file__).parent.resolve() / "sql/get_latest_versions.sql") as f:
    get_latest_versions_sql = f.read()


class EnvironmentFeatureVersionManager(SoftDeleteManager):
    def get_latest_versions(self, environment: "Environment") -> RawQuerySet:
        """
        Get the latest EnvironmentFeatureVersion objects
        for a given environment.
        """
        return self.raw(
            get_latest_versions_sql, params={"environment_id": environment.id}
        )
