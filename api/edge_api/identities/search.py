import enum
from dataclasses import dataclass

IDENTIFIER_ATTRIBUTE = "identifier"
DASHBOARD_ALIAS_ATTRIBUTE = "dashboard_alias"
DASHBOARD_ALIAS_SEARCH_PREFIX = f"{DASHBOARD_ALIAS_ATTRIBUTE}:"

IDENTIFIER_INDEX_NAME = "environment_api_key-identifier-index"
DASHBOARD_ALIAS_INDEX_NAME = "environment_api_key-dashboard_alias-index-v2"


class EdgeIdentitySearchType(enum.Enum):
    EQUAL = "EQUAL"
    BEGINS_WITH = "BEGINS_WITH"


@dataclass
class EdgeIdentitySearchData:
    search_term: str
    search_type: EdgeIdentitySearchType
    search_attribute: str

    @property
    def dynamo_search_method(self):  # type: ignore[no-untyped-def]
        return (
            "eq" if self.search_type == EdgeIdentitySearchType.EQUAL else "begins_with"
        )

    @property
    def dynamo_index_name(self):  # type: ignore[no-untyped-def]
        if self.search_attribute == DASHBOARD_ALIAS_ATTRIBUTE:
            return DASHBOARD_ALIAS_INDEX_NAME
        return IDENTIFIER_INDEX_NAME
