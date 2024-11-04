import typing
from datetime import datetime

from pydantic import BaseModel


class LicenceInformation(BaseModel):
    organisation_name: str
    plan_id: str

    department_name: typing.Optional[str] = None
    expiry_date: typing.Optional[datetime] = None

    num_seats: int
    num_projects: int
    num_api_calls: typing.Optional[int] = (
        None  # required to support private cloud installs
    )
