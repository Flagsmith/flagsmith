from typing import cast

from django.conf import settings

if settings.SCIM_INSTALLED:
    import pytest
    from pytest_mock import MockerFixture
    from rest_framework.test import APIClient
    from scim.mappers import map_issued_token_to_bearer
    from scim.services import create_scim_configuration_for_organisation

    from organisations.models import Organisation

    @pytest.fixture()
    def scim_organisation(db: None) -> Organisation:
        return cast(Organisation, Organisation.objects.create(name="SCIM Org"))

    @pytest.fixture()
    def enterprise_scim_organisation(
        scim_organisation: Organisation, mocker: MockerFixture
    ) -> Organisation:
        mocker.patch.object(
            Organisation, "has_enterprise_subscription", return_value=True
        )
        return scim_organisation

    @pytest.fixture()
    def scim_bearer_for_enterprise_org(
        enterprise_scim_organisation: Organisation,
    ) -> str:
        issued = create_scim_configuration_for_organisation(
            enterprise_scim_organisation
        )
        return map_issued_token_to_bearer(issued.issued_token)

    @pytest.fixture()
    def scim_bearer_for_non_enterprise_org(
        scim_organisation: Organisation, mocker: MockerFixture
    ) -> str:
        mocker.patch.object(
            Organisation, "has_enterprise_subscription", return_value=False
        )
        issued = create_scim_configuration_for_organisation(scim_organisation)
        return map_issued_token_to_bearer(issued.issued_token)

    @pytest.fixture()
    def scim_client() -> APIClient:
        return APIClient()
