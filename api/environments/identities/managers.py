from typing import TYPE_CHECKING

from django.db.models import Manager

from environments.identities.services import replace_identity_environment

if TYPE_CHECKING:
    from typing import Iterable

    from django.db.models import Prefetch, QuerySet

    from environments.identities.models import Identity
    from environments.models import Environment


class IdentityManager(Manager["Identity"]):
    def get_by_natural_key(
        self,
        identifier: str,
        environment_api_key: str,
    ) -> "Identity":
        return self.get(identifier=identifier, environment__api_key=environment_api_key)

    def get_or_create_for_sdk(
        self,
        identifier: str,
        environment: "Environment",
    ) -> "tuple[Identity, bool]":
        identity, created = self.with_traits().get_or_create(
            identifier=identifier,
            environment=environment,
        )
        replace_identity_environment(identity, environment)
        return identity, created

    def with_traits(
        self,
        extra_prefetch_related: "Iterable[str | Prefetch] | None" = None,  # type: ignore[type-arg]
    ) -> "QuerySet[Identity]":
        return self.prefetch_related(
            "identity_traits",
            *(extra_prefetch_related or []),
        )
