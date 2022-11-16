import json

import responses


@responses.activate
def test_pipedrive_api_client_create_lead(
    pipedrive_api_client, pipedrive_base_url, pipedrive_api_token
):
    # Given
    example_response_file_name = "example_api_responses/create_lead.json"

    # obtained from file above, duplicated here to simplify test
    title = "Johnny Bravo"
    organization_id = 1
    lead_id = "11c18740-659d-11ed-b6e9-ab3d83dc63a5"

    with open(example_response_file_name) as f:
        responses.add(
            method=responses.POST,
            url=f"{pipedrive_base_url}/leads",
            json=json.load(f),
            status=201,
        )

    # When
    lead = pipedrive_api_client.create_lead(
        title=title, organization_id=organization_id
    )

    # Then
    assert len(responses.calls) == 1
    call = responses.calls[0]
    request_body = json.loads(call.request.body.decode("utf-8"))
    assert request_body == {"title": title, "organization_id": organization_id}
    assert call.request.params["api_token"] == pipedrive_api_token

    assert lead.id == lead_id
    assert lead.title == title
    assert lead.organization_id == organization_id


@responses.activate
def test_pipedrive_api_client_create_organization(
    pipedrive_api_client, pipedrive_base_url, pipedrive_api_token
):
    # Given
    example_response_file_name = "example_api_responses/create_organization.json"

    # obtained from file above, duplicated here to simplify test
    name = "Test org"
    organization_id = 1
    organization_field_key = "1ebc98029a711f60a51b7169b5784fa85d83f4cc"
    organization_field_value = "some-value"

    with open(example_response_file_name) as f:
        responses.add(
            method=responses.POST,
            url=f"{pipedrive_base_url}/organizations",
            json=json.load(f),
            status=201,
        )

    # When
    organization = pipedrive_api_client.create_organization(
        name=name,
        organization_fields={organization_field_key: organization_field_value},
    )

    # Then
    assert len(responses.calls) == 1
    call = responses.calls[0]
    request_body = json.loads(call.request.body.decode("utf-8"))
    assert request_body == {
        "name": name,
        organization_field_key: organization_field_value,
    }
    assert call.request.params["api_token"] == pipedrive_api_token

    assert organization.id == organization_id
    assert organization.name == name
    # TODO: can we get the custom fields applied to the org model?


@responses.activate
def test_pipedrive_api_client_search_organizations(
    pipedrive_api_client, pipedrive_base_url, pipedrive_api_token
):
    # Given
    example_response_file_name = "example_api_responses/search_organizations.json"

    # obtained from file above, duplicated here to simplify test
    search_term = "Test org"
    result_organization_name = "Test org"
    result_organization_id = 1

    with open(example_response_file_name) as f:
        responses.add(
            method=responses.GET,
            url=f"{pipedrive_base_url}/organizations/search",
            json=json.load(f),
            status=200,
        )

    # When
    organizations = pipedrive_api_client.search_organizations(search_term=search_term)

    # Then
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.params["api_token"] == pipedrive_api_token
    assert call.request.params["term"] == search_term

    assert len(organizations) == 1
    assert organizations[0].name == result_organization_name
    assert organizations[0].id == result_organization_id


@responses.activate
def test_pipedrive_api_client_create_organization_field(
    pipedrive_api_client, pipedrive_base_url, pipedrive_api_token
):
    # Given
    example_response_file_name = "example_api_responses/create_organization_field.json"

    # obtained from file above, duplicated here to simplify test
    organization_field_name = "new-field"
    organization_field_key = "1ebc98029a711f60a51b7169b5784fa85d83f4cc"

    with open(example_response_file_name) as f:
        responses.add(
            method=responses.POST,
            url=f"{pipedrive_base_url}/organizationFields",
            json=json.load(f),
            status=201,
        )

    # When
    organization_field = pipedrive_api_client.create_organization_field(
        name=organization_field_name
    )

    # Then
    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.params["api_token"] == pipedrive_api_token

    assert organization_field.key == organization_field_key
    assert organization_field.name == organization_field_name
