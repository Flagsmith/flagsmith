from typing import TYPE_CHECKING, Iterable

from django.db.models import Manager

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
