from core.apps import BaseAppConfig


class EnvironmentPermissionsConfig(BaseAppConfig):
    default = True
    name = "environments.permissions"
    label = "environment_permissions"
