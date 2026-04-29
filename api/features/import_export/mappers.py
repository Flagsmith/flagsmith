from features.import_export.types import FeatureExportData
from features.models import Feature
from projects.models import Project


def map_feature_export_data_to_feature(
    feature_data: FeatureExportData, project: Project
) -> Feature:
    return Feature(
        name=feature_data["name"],
        project=project,
        initial_value=feature_data["initial_value"],
        is_server_key_only=feature_data["is_server_key_only"],
        default_enabled=feature_data["default_enabled"],
    )
