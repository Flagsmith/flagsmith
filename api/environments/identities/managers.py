from typing import TYPE_CHECKING, Iterable

from django.db.models import Manager, Prefetch, QuerySet

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.models import Environment
    from integrations.integration import IntegrationConfig


class IdentityManager(Manager["Identity"]):
    def get_by_natural_key(self, identifier, environment_api_key):
        return self.get(identifier=identifier, environment__api_key=environment_api_key)

    def get_or_create_for_sdk(
        self,
        identifier: str,
        environment: "Environment",
        integrations: Iterable["IntegrationConfig"],
    ) -> tuple["Identity", bool]:
        return (
            self.select_related(
                "environment",
                "environment__project",
                *[
                    f"environment__{integration['relation_name']}"
                    for integration in integrations
                ],
            )
            .prefetch_related("identity_traits")
            .get_or_create(identifier=identifier, environment=environment)
        )

    def only_overrides(self) -> QuerySet["Identity"]:
        """
        Only include identities with overridden features.
        """
        return self.prefetch_related(
            Prefetch("identity_features"),
        ).filter(identity_features__isnull=False)
