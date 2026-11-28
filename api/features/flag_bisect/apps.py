from core.apps import BaseAppConfig


class FlagBisectConfig(BaseAppConfig):
    name = "features.flag_bisect"
    label = "flag_bisect"
    default = True
