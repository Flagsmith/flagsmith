from typing import Optional

from pydantic import BaseModel


class IntegrationModel(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    entity_selector: Optional[str] = None
