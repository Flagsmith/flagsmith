from pydantic import BaseModel, Field

from util.engine_models.identities.traits.types import ContextValue


class TraitModel(BaseModel):
    trait_key: str
    trait_value: ContextValue = Field(...)
