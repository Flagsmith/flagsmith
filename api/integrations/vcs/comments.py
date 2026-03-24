import typing

from core.helpers import get_current_site_url
from integrations.vcs.constants import (
    DELETED_FEATURE_TEXT,
    DELETED_SEGMENT_OVERRIDE_TEXT,
    FEATURE_ENVIRONMENT_URL,
    FEATURE_TABLE_HEADER,
    FEATURE_TABLE_ROW,
    LINK_FEATURE_TITLE,
    LINK_SEGMENT_TITLE,
    UPDATED_FEATURE_TEXT,
)


def generate_body_comment(
    name: str,
    event_type: str,
    feature_id: int,
    feature_states: list[dict[str, typing.Any]],
    unlinked_feature_text: str,
    project_id: int | None = None,
    segment_name: str | None = None,
) -> str:
    """Generate a markdown comment for a VCS issue/PR/MR.

    This is shared between GitHub and GitLab integrations. The only
    difference is the unlinked_feature_text which uses "PR" for GitHub
    and "MR" for GitLab.
    """
    if event_type == "FLAG_DELETED":
        return DELETED_FEATURE_TEXT % (name)

    if event_type == "FEATURE_EXTERNAL_RESOURCE_REMOVED":
        return unlinked_feature_text % (name)

    if event_type == "SEGMENT_OVERRIDE_DELETED" and segment_name is not None:
        return DELETED_SEGMENT_OVERRIDE_TEXT % (segment_name, name)

    result = ""
    if event_type == "FLAG_UPDATED":
        result = UPDATED_FEATURE_TEXT % (name)
    else:
        result = LINK_FEATURE_TITLE % (name)

    last_segment_name = ""
    if len(feature_states) > 0 and not feature_states[0].get("segment_name"):
        result += FEATURE_TABLE_HEADER

    for fs in feature_states:
        feature_value = fs.get("feature_state_value")
        tab = "segment-overrides" if fs.get("segment_name") is not None else "value"
        environment_link_url = FEATURE_ENVIRONMENT_URL % (
            get_current_site_url(),
            project_id,
            fs.get("environment_api_key"),
            feature_id,
            tab,
        )
        if (
            fs.get("segment_name") is not None
            and fs["segment_name"] != last_segment_name
        ):
            result += "\n" + LINK_SEGMENT_TITLE % (fs["segment_name"])
            last_segment_name = fs["segment_name"]
            result += FEATURE_TABLE_HEADER
        table_row = FEATURE_TABLE_ROW % (
            fs["environment_name"],
            environment_link_url,
            "✅ Enabled" if fs["enabled"] else "❌ Disabled",
            f"`{feature_value}`" if feature_value else "",
            fs["last_updated"],
        )
        result += table_row

    return result
