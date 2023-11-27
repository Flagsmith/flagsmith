from typing import TYPE_CHECKING

from django.db.models import Manager

from integrations.integration import IDENTITY_INTEGRATIONS

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.models import Environment


class IdentityManager(Manager):
    def get_by_natural_key(self, identifier, environment_api_key):
        return self.get(identifier=identifier, environment__api_key=environment_api_key)

    def get_or_create_for_sdk(
        self,
        identifier: str,
        environment: "Environment",
    ) -> tuple["Identity", bool]:
        return (
            self.select_related(
                "environment",
                "environment__project",
                *[
                    f"environment__{integration['relation_name']}"
                    for integration in IDENTITY_INTEGRATIONS
                ],
            )
            .prefetch_related("identity_traits")
            .get_or_create(identifier=identifier, environment=environment)
        )
