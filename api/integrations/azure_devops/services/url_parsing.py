import re
from typing import NamedTuple
from urllib.parse import unquote, urlparse

# Path captures (after stripping query/fragment, normalising trailing slash):
#   /{org_or_collection}/{project}/_git/{repo}/pullrequest/{id}
#   /{org_or_collection}/{project}/_workitems/edit/{id}
#
# For ADO cloud, {org_or_collection} is a single org segment (e.g. "test-org").
# For Azure DevOps Server (on-prem), {org_or_collection} is a collection name,
# and the same path pattern applies under whatever host the server runs on.

_PR_PATH_PATTERN = re.compile(
    r"^/(?P<org_or_collection>[^/]+)/(?P<project>[^/]+)"
    r"/_git/(?P<repo>[^/]+)/pullrequest/(?P<pr_id>\d+)/?$"
)

_WORK_ITEM_PATH_PATTERN = re.compile(
    r"^/(?P<org_or_collection>[^/]+)/(?P<project>[^/]+)"
    r"/_workitems/edit/(?P<work_item_id>\d+)/?$"
)


class AdoPullRequestRef(NamedTuple):
    organisation_root: str
    project: str
    repository: str
    pull_request_id: int


class AdoWorkItemRef(NamedTuple):
    organisation_root: str
    project: str
    work_item_id: int


def parse_pull_request_url(url: str | None) -> AdoPullRequestRef | None:
    """Return a structured reference for an Azure DevOps pull-request URL,
    or ``None`` if the URL does not match the cloud or on-prem PR shape.
    Parsing never raises.
    """
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    match = _PR_PATH_PATTERN.match(parsed.path)
    if not match:
        return None
    return AdoPullRequestRef(
        organisation_root=f"{parsed.scheme}://{parsed.netloc}/{match.group('org_or_collection')}",
        project=unquote(match.group("project")),
        repository=unquote(match.group("repo")),
        pull_request_id=int(match.group("pr_id")),
    )


def parse_work_item_url(url: str | None) -> AdoWorkItemRef | None:
    """Return a structured reference for an Azure DevOps work-item URL,
    or ``None`` if the URL does not match the cloud or on-prem work-item
    shape. Parsing never raises.
    """
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    match = _WORK_ITEM_PATH_PATTERN.match(parsed.path)
    if not match:
        return None
    return AdoWorkItemRef(
        organisation_root=f"{parsed.scheme}://{parsed.netloc}/{match.group('org_or_collection')}",
        project=unquote(match.group("project")),
        work_item_id=int(match.group("work_item_id")),
    )
