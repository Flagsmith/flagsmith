import typing
from pathlib import Path

from django.db.models.query import QuerySet, RawQuerySet
from softdelete.models import SoftDeleteManager

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.versioning.models import EnvironmentFeatureVersion


with open(Path(__file__).parent.resolve() / "sql/get_latest_versions.sql") as f:
    get_latest_versions_sql = f.read()


class EnvironmentFeatureVersionManager(SoftDeleteManager):
    def get_latest_versions(self, environment: "Environment") -> RawQuerySet:
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment.
        """
        return self.raw(
            get_latest_versions_sql, params={"environment_id": environment.id}
        )

    def get_latest_versions_as_queryset(
        self, environment: "Environment"
    ) -> QuerySet["EnvironmentFeatureVersion"]:
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment
        as a concrete QuerySet.

        Note that it is often required to return the proper QuerySet to carry out
        operations on the ORM object.
        """
        return self.filter(
            uuid__in=[
                efv.uuid
                for efv in EnvironmentFeatureVersion.objects.get_latest_versions(self)
            ]
        )
