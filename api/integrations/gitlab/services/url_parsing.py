import re
from urllib.parse import urlparse

_RESOURCE_PATH_PATTERN = re.compile(
    r"^/(?P<path>.+?)/-/(?:issues|work_items|merge_requests)/\d+/?$"
)


def parse_project_path(resource_url: str | None) -> str | None:
    """Return the GitLab project's URL-encodable path (``group/subgroup/project``)
    from an issue or MR URL, or ``None`` if the URL isn't in the expected shape.
    """
    if not resource_url:
        return None
    match = _RESOURCE_PATH_PATTERN.match(urlparse(resource_url).path)
    return match.group("path") if match else None
