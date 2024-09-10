import enum
from dataclasses import dataclass

IDENTIFIER_ATTRIBUTE = "identifier"
DASHBOARD_ALIAS_ATTRIBUTE = "dashboard_alias"
DASHBOARD_ALIAS_SEARCH_PREFIX = f"{DASHBOARD_ALIAS_ATTRIBUTE}:"


class EdgeIdentitySearchType(enum.Enum):
    EQUAL = "EQUAL"
    BEGINS_WITH = "BEGINS_WITH"


@dataclass
class EdgeIdentitySearchData:
    search_term: str
    search_type: EdgeIdentitySearchType
    search_attribute: str

    @property
    def dynamo_search_method(self):
        return (
            "eq" if self.search_type == EdgeIdentitySearchType.EQUAL else "begins_with"
        )

    @property
    def dynamo_index_name(self):
        return f"environment_api_key-{self.search_attribute}-index"
