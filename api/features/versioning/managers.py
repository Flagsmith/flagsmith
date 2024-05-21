from pathlib import Path

from django.db.models.query import RawQuerySet
from softdelete.models import SoftDeleteManager

with open(
    Path(__file__).parent.resolve() / "sql/get_latest_versions_by_environment_id.sql"
) as f:
    get_latest_versions_by_environment_id_sql = f.read()

with open(
    Path(__file__).parent.resolve()
    / "sql/get_latest_versions_by_environment_api_key.sql"
) as f:
    get_latest_versions_by_environment_api_key_sql = f.read()


class EnvironmentFeatureVersionManager(SoftDeleteManager):
    def get_latest_versions_by_environment_id(self, environment_id: int) -> RawQuerySet:
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment.
        """
        return self.raw(
            get_latest_versions_by_environment_id_sql,
            params={"environment_id": environment_id},
        )

    def get_latest_versions_by_environment_api_key(
        self, environment_api_key: str
    ) -> RawQuerySet:
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment.
        """
        return self.raw(
            get_latest_versions_by_environment_api_key_sql,
            params={"api_key": environment_api_key},
        )
