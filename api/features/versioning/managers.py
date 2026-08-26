import typing
from pathlib import Path

from django.db.models.query import QuerySet, RawQuerySet
from django.utils import timezone
from softdelete.models import SoftDeleteManager  # type: ignore[import-untyped]

if typing.TYPE_CHECKING:
    from features.versioning.models import EnvironmentFeatureVersion


with open(Path(__file__).parent.resolve() / "sql/get_latest_versions.sql") as f:
    get_latest_versions_sql = f.read()


class EnvironmentFeatureVersionManager(SoftDeleteManager):  # type: ignore[misc]
    def get_superseding_versions(
        self,
        feature_id: typing.Any,
        environment_id: typing.Any,
        live_from: typing.Any,
    ) -> QuerySet["EnvironmentFeatureVersion"]:
        """
        Get the versions of a flag that have gone live since the given time.

        A version is superseded once another has gone live after it, so
        `~Exists(get_superseding_versions(..., live_from=<the version's
        live_from>))` identifies the version currently being served. Versions
        scheduled to go live later are excluded, since they are not serving
        anything yet.

        Ordering by when versions went live rather than when they were created
        matches what the SDKs serve — see
        https://github.com/Flagsmith/flagsmith/issues/8127.

        The arguments are loosely typed so that callers can pass `OuterRef`
        expressions and use this as a correlated subquery, which avoids
        querying per environment.
        """
        return self.filter(  # type: ignore[no-any-return]
            feature_id=feature_id,
            environment_id=environment_id,
            published_at__isnull=False,
            live_from__lte=timezone.now(),
            live_from__gt=live_from,
        )

    def get_latest_versions_by_environment_id(self, environment_id: int) -> RawQuerySet:  # type: ignore[type-arg]
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment.
        """
        return self._get_latest_versions(environment_id=environment_id)

    def get_latest_versions_by_environment_api_key(
        self, environment_api_key: str
    ) -> RawQuerySet:  # type: ignore[type-arg]
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment.
        """
        return self._get_latest_versions(environment_api_key=environment_api_key)

    def get_latest_versions_as_queryset(
        self, environment_id: int
    ) -> QuerySet["EnvironmentFeatureVersion"]:
        """
        Get the latest EnvironmentFeatureVersion objects for a given environment
        as a concrete QuerySet.

        Note that it is often required to return the proper QuerySet to carry out
        operations on the ORM object.
        """
        return self.filter(  # type: ignore[no-any-return]
            uuid__in=[
                efv.uuid
                for efv in self._get_latest_versions(environment_id=environment_id)
            ]
        )

    def _get_latest_versions(
        self,
        environment_id: int = None,  # type: ignore[assignment]
        environment_api_key: str = None,  # type: ignore[assignment]
    ) -> RawQuerySet:  # type: ignore[type-arg]
        assert (environment_id or environment_api_key) and not (
            environment_id and environment_api_key
        ), "Must provide exactly one of environment_id or environment_api_key"

        return self.raw(  # type: ignore[no-any-return]
            get_latest_versions_sql,
            params={
                "environment_id": environment_id,
                "api_key": environment_api_key,
                # TODO:
                #  It seems as though there is a timezone issue when using postgres's
                #  built in now() function, so we pass in the current time from python.
                #  Using <= now() in the SQL query returns incorrect results.
                #  More investigation is needed here to understand the cause.
                "live_from_before": timezone.now().isoformat(),
            },
        )
