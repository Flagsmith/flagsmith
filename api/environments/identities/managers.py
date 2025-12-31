from typing import TYPE_CHECKING

from django.db.models import Manager

if TYPE_CHECKING:
    from typing import Iterable

    from django.db.models import Prefetch, QuerySet

    from environments.identities.models import Identity
    from environments.models import Environment
    from integrations.integration import IntegrationConfig


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
        return self.with_context().get_or_create(
            identifier=identifier,
            environment=environment,
        )

    def with_context(
        self,
        integrations: "Iterable[IntegrationConfig] | None" = None,
        extra_select_related: "Iterable[str] | None" = None,
        extra_prefetch_related: "Iterable[str | Prefetch] | None" = None,  # type: ignore[type-arg]
    ) -> "QuerySet[Identity]":
        from integrations.integration import IDENTITY_INTEGRATIONS

        return self.select_related(
            "environment",
            "environment__project",
            *(
                f"environment__{integration['relation_name']}"
                for integration in (integrations or IDENTITY_INTEGRATIONS)
            ),
            *(extra_select_related or []),
        ).prefetch_related(
            "identity_traits",
            *(extra_prefetch_related or []),
        )
