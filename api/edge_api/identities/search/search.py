from typing import NamedTuple

import boto3
from pyathena import connect
from pyathena.cursor import DictCursor

athena = boto3.client("athena")


class EdgeIdentitySearchResult(NamedTuple):
    identity_id: str
    trait_name: str
    trait_value: str


def get_edge_identities_by_trait(
    environment_api_key: str, trait_key: str, trait_value: str
) -> list[EdgeIdentitySearchResult]:
    cursor = connect(
        s3_staging_dir="s3://identity-by-traits-data-results/traits/",
        region_name="eu-west-2",
        cursor_class=DictCursor,
    ).cursor()

    query_string = (
        f"SELECT identity_id, trait_name, trait_value "
        f"FROM IdentityTraits.identity_traits "
        f"WHERE environment_api_key='{environment_api_key}' "
        f"AND trait_name='{trait_key}' "
        f"AND trait_value='{trait_value}'"
    )

    cursor.execute(query_string)
    results = cursor.fetchall()
    return [EdgeIdentitySearchResult(*result.values()) for result in results]


if __name__ == "__main__":
    matching_identities = get_edge_identities_by_trait(
        environment_api_key="api_key_1",
        trait_key="app_version",
        trait_value="v1.1",
    )
    print(matching_identities)
