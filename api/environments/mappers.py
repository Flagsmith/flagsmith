from typing import TYPE_CHECKING, Any

from flag_engine.api.document_builders import build_environment_document

if TYPE_CHECKING:
    from environments.models import Environment


def map_environment_to_document(environment: "Environment") -> dict[str, Any]:
    environment.project.server_key_only_feature_ids: list[int] = [
        feature.id
        for feature_state in environment.feature_states.all()
        if (feature := feature_state.feature).is_server_key_only
    ]
    return build_environment_document(environment)
