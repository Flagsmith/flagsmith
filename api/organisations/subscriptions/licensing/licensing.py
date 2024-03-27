import os
from datetime import datetime

from pydantic import BaseModel

from organisations.models import UserOrganisation
from projects.models import Project


class LicenceInformation(BaseModel):
    licensee: str
    plan_id: str
    expiry_date: datetime

    # TODO: should these live in a nested object?
    num_seats: int
    num_projects: int  # TODO: what about Flagsmith on Flagsmith project?

    def get_remaining_seats(self) -> int:
        return self.num_seats - UserOrganisation.objects.count()

    def get_remaining_projects(self) -> int:
        return self.num_projects - Project.objects.count()


def licence_file_exists(licence_file_path: str = "") -> bool:
    return os.path.isfile(licence_file_path)


def read_license_file(licence_file_path: str = "") -> LicenceInformation:
    return LicenceInformation.parse_file(licence_file_path)
