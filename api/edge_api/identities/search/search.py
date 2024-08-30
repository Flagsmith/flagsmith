import time
from typing import NamedTuple

import boto3

athena = boto3.client("athena")


class EdgeIdentitySearchResult(NamedTuple):
    edge_identity_uuid: str
    trait_name: str
    trait_value: str


def get_edge_identities_by_trait(
    environment_api_key: str, trait_key: str, trait_value: str
) -> list[EdgeIdentitySearchResult]:
    query_string = (
        f"SELECT identity_id, trait_name, trait_value "
        f"FROM IdentityTraits.identity_traits "
        f"WHERE environment_api_key='{environment_api_key}' "
        f"AND trait_name='{trait_key}' "
        f"AND trait_value='{trait_value}'"
    )
    exec_response = athena.start_query_execution(
        QueryString=query_string,
        ResultConfiguration={
            "OutputLocation": "s3://identity-by-traits-data-results/traits/"
        },
    )
    query_execution_id = exec_response["QueryExecutionId"]

    while True:
        status_response = athena.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        status = status_response["QueryExecution"]["Status"]["State"]
        if status == "SUCCEEDED":
            break
        time.sleep(0.5)

    results_response = athena.get_query_results(QueryExecutionId=query_execution_id)

    edge_identities = []
    for result in results_response["ResultSet"]["Rows"][1:]:
        edge_identities.append(
            EdgeIdentitySearchResult(
                result["Data"][0]["VarCharValue"],
                result["Data"][1]["VarCharValue"],
                result["Data"][2]["VarCharValue"],
            )
        )

    assert edge_identities


if __name__ == "__main__":
    matching_identities = get_edge_identities_by_trait(
        environment_api_key="HxiPySrNFWftNmCfhGUxFA",
        trait_key="app_version",
        trait_value="1.9.4",
    )
    print(matching_identities)
