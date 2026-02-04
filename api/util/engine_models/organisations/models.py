from pydantic import BaseModel


class OrganisationModel(BaseModel):
    id: int
    name: str
    feature_analytics: bool = False
    stop_serving_flags: bool = False
    persist_trait_data: bool = True
