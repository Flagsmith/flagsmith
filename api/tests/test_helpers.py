from typing import Any

from flag_engine.segments.types import ConditionOperator


def generate_segment_data(
    segment_name: str,
    project_id: int,
    condition_tuples: list[tuple[str, ConditionOperator, str]],
) -> dict[str, Any]:
    return {
        "name": segment_name,
        "project": project_id,
        "rules": [
            {
                "type": "ALL",
                "rules": [
                    {
                        "type": "ANY",
                        "rules": [],
                        "conditions": [
                            {
                                "property": condition_tuple[0],
                                "operator": condition_tuple[1],
                                "value": condition_tuple[2],
                            }
                            for condition_tuple in condition_tuples
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }


def fix_issue_3869():
    """
    Hack to get around Pydantic issue with Freeze Gun.

    https://github.com/Flagsmith/flagsmith/issues/3869
    """
    from environments.sdk.schemas import (  # noqa: F401
        SDKEnvironmentDocumentModel,
    )
