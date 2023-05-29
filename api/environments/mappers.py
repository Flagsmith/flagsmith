from typing import TYPE_CHECKING, Any

from flag_engine.api.document_builders import build_environment_document

if TYPE_CHECKING:
    from environments.models import Environment


def map_environment_to_document(environment: "Environment") -> dict[str, Any]:
    """
    Maps Core API's `environments.models.Environment` mode instance to the
    flag_engine environment document.
    Before building the document, takes care of resolving relationships and
    feature versions.

    :param Environment environment: the environment to map
    :rtype dict[str, Any]
    """
    # TODO @khvn26 Migrate flag_engine logic to here https://github.com/Flagsmith/flagsmith/issues/2079
    environment.project.server_key_only_feature_ids: list[int] = [
        feature.id
        for feature_state in environment.feature_states.all()
        if (feature := feature_state.feature).is_server_key_only
    ]
    return build_environment_document(environment)
