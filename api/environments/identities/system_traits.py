import typing

from django.db.models import F, Func, Value
from django.db.models.fields.json import JSONField

from environments.dynamodb import DynamoIdentityWrapper
from environments.identities.models import Identity

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project


# Postgres merges and drops a key in a single statement, so writing one
# identity's trait never reads, locks, or overwrites another writer's keys.
class _JSONBMerge(Func):
    arg_joiner = " || "
    template = "%(expressions)s"
    output_field = JSONField()


class _JSONBDropKey(Func):
    arg_joiner = " - "
    template = "%(expressions)s"
    output_field = JSONField()


def identities_stored_in_dynamodb(project: "Project") -> bool:
    return bool(project.enable_dynamo_db and DynamoIdentityWrapper().is_enabled)


def _set_system_trait_for_edge_identities(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    identity_wrapper = DynamoIdentityWrapper()
    for identifier in identifiers:
        identity_wrapper.set_system_trait(
            environment_api_key=environment.api_key,
            identifier=identifier,
            trait_key=trait_key,
        )


def _unset_system_trait_for_edge_identities(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    identity_wrapper = DynamoIdentityWrapper()
    for identifier in identifiers:
        identity_wrapper.unset_system_trait(
            environment_api_key=environment.api_key,
            identifier=identifier,
            trait_key=trait_key,
        )


def _set_system_trait_for_postgres_identities(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    # An identity that has never identified still gets the trait, so that it is
    # already in place the first time it does.
    Identity.objects.bulk_create(
        [
            Identity(environment_id=environment.id, identifier=identifier)
            for identifier in identifiers
        ],
        ignore_conflicts=True,
    )
    Identity.objects.filter(
        environment_id=environment.id, identifier__in=identifiers
    ).update(
        system_traits=_JSONBMerge(
            F("system_traits"), Value({trait_key: True}, JSONField())
        )
    )


def _unset_system_trait_for_postgres_identities(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    Identity.objects.filter(
        environment_id=environment.id, identifier__in=identifiers
    ).update(system_traits=_JSONBDropKey(F("system_traits"), Value(trait_key)))


def set_system_trait(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    if not identifiers:
        return
    if identities_stored_in_dynamodb(environment.project):
        _set_system_trait_for_edge_identities(environment, trait_key, identifiers)
    else:
        _set_system_trait_for_postgres_identities(environment, trait_key, identifiers)


def unset_system_trait(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    if not identifiers:
        return
    if identities_stored_in_dynamodb(environment.project):
        _unset_system_trait_for_edge_identities(environment, trait_key, identifiers)
    else:
        _unset_system_trait_for_postgres_identities(environment, trait_key, identifiers)
