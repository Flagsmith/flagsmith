from core.apps import BaseAppConfig


class OrganisationPermissionsConfig(BaseAppConfig):
    default = True
    name = "organisations.permissions"
    label = "organisation_permissions"
