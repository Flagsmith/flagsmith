import typing

from environments.identities.models import Identity
from environments.identities.traits.models import Trait


def generate_trait_data_item(  # type: ignore[no-untyped-def]
    trait_key: str = "trait_key",
    trait_value: typing.Any = "trait_value",
    transient: bool = False,
):
    return {
        "trait_key": trait_key,
        "trait_value": trait_value,
        "transient": transient,
    }


def create_trait_for_identity(  # type: ignore[no-untyped-def]
    identity: Identity, trait_key: str, trait_value: typing.Any
):
    trait_value_data = Trait.generate_trait_value_data(trait_value)
    return Trait.objects.create(
        identity=identity, trait_key=trait_key, **trait_value_data
    )


def get_trait_from_list_by_key(trait_key: str, traits: list):  # type: ignore[no-untyped-def,type-arg]
    return next(filter(lambda trait: trait.trait_key == trait_key, traits))
