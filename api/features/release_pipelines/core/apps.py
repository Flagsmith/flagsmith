from core.apps import BaseAppConfig


class ReleasePipelineConfig(BaseAppConfig):
    name = "features.release_pipelines.core"
    label = "release_pipelines_core"
    default = True
