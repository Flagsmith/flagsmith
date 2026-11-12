from core.apps import BaseAppConfig


class FeatureDependenciesConfig(BaseAppConfig):
    name = "features.dependencies"
    label = "feature_dependencies"
    default = True
