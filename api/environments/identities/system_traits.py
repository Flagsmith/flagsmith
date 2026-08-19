"""Setting and clearing system traits on an environment's identities.

A system trait is owned by Flagsmith rather than the customer — cohort
membership, for example. Segment conditions read it exactly like a user trait,
but SDKs can neither see nor write it. Membership is the only value we store,
so the value is always `True`; callers name the trait and the identities, not
the store holding them.

Identities live in DynamoDB documents for edge projects and in Postgres rows
for everyone else, so each operation has an implementation per store. Keeping
both here means one contract, and one set of tests, rather than two callers
that happen to agree.
"""

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


def set_system_trait(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    if not identifiers:
        return
    if identities_stored_in_dynamodb(environment.project):
        identity_wrapper = DynamoIdentityWrapper()
        for identifier in identifiers:
            identity_wrapper.set_system_trait(
                environment_api_key=environment.api_key,
                identifier=identifier,
                trait_key=trait_key,
            )
        return
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


def unset_system_trait(
    environment: "Environment", trait_key: str, identifiers: list[str]
) -> None:
    if not identifiers:
        return
    if identities_stored_in_dynamodb(environment.project):
        identity_wrapper = DynamoIdentityWrapper()
        for identifier in identifiers:
            identity_wrapper.unset_system_trait(
                environment_api_key=environment.api_key,
                identifier=identifier,
                trait_key=trait_key,
            )
        return
    Identity.objects.filter(
        environment_id=environment.id, identifier__in=identifiers
    ).update(system_traits=_JSONBDropKey(F("system_traits"), Value(trait_key)))
