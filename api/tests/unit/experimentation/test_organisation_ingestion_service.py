import pytest
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from experimentation import organisation_ingestion_service
from experimentation.dataclasses import IngestionInfrastructure
from experimentation.models import (
    IngestionInfrastructureStatus,
    OrganisationIngestionInfrastructure,
)
from organisations.models import Organisation

INFRASTRUCTURE = IngestionInfrastructure(
    bucket_name="flagsmith-events-lake-org-1-123456789012-eu-west-2-an",
    stream_name="events-ingestion-org-1",
)


def test_enable_ingestion_for_organisation__fresh__provisions_and_records(
    organisation: Organisation,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    provision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".provision_ingestion_infrastructure",
        return_value=INFRASTRUCTURE,
    )

    # When
    infrastructure = organisation_ingestion_service.enable_ingestion_for_organisation(
        organisation
    )

    # Then
    provision.assert_called_once_with(organisation.id)
    assert infrastructure.status == IngestionInfrastructureStatus.CREATED
    assert infrastructure.bucket_name == INFRASTRUCTURE.bucket_name
    assert infrastructure.stream_name == INFRASTRUCTURE.stream_name
    assert {
        "level": "info",
        "event": "ingestion_infra.provisioned",
        "organisation__id": organisation.id,
        "bucket__name": INFRASTRUCTURE.bucket_name,
        "stream__name": INFRASTRUCTURE.stream_name,
    } in log.events


def test_enable_ingestion_for_organisation__already_created__does_not_reprovision(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    existing = OrganisationIngestionInfrastructure.objects.create(
        organisation=organisation,
        status=IngestionInfrastructureStatus.CREATED,
        bucket_name=INFRASTRUCTURE.bucket_name,
        stream_name=INFRASTRUCTURE.stream_name,
    )
    provision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".provision_ingestion_infrastructure",
    )

    # When
    infrastructure = organisation_ingestion_service.enable_ingestion_for_organisation(
        organisation
    )

    # Then
    provision.assert_not_called()
    assert infrastructure == existing


def test_enable_ingestion_for_organisation__provision_fails__marks_errored_and_reraises(
    organisation: Organisation,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".provision_ingestion_infrastructure",
        side_effect=RuntimeError("boom"),
    )

    # When / Then
    with pytest.raises(RuntimeError, match="boom"):
        organisation_ingestion_service.enable_ingestion_for_organisation(organisation)

    infrastructure = OrganisationIngestionInfrastructure.objects.get(
        organisation=organisation
    )
    assert infrastructure.status == IngestionInfrastructureStatus.ERRORED
    assert any(
        event["event"] == "ingestion_infra.provision_failed" for event in log.events
    )


def test_disable_ingestion_for_organisation__created__deprovisions_and_deletes_row(
    organisation: Organisation,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    OrganisationIngestionInfrastructure.objects.create(
        organisation=organisation,
        status=IngestionInfrastructureStatus.CREATED,
        bucket_name=INFRASTRUCTURE.bucket_name,
        stream_name=INFRASTRUCTURE.stream_name,
    )
    deprovision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".deprovision_ingestion_infrastructure",
    )

    # When
    organisation_ingestion_service.disable_ingestion_for_organisation(organisation.id)

    # Then
    deprovision.assert_called_once_with(organisation.id)
    assert not OrganisationIngestionInfrastructure.objects.filter(
        organisation=organisation
    ).exists()
    assert {
        "level": "info",
        "event": "ingestion_infra.torn_down",
        "organisation__id": organisation.id,
    } in log.events


def test_disable_ingestion_for_organisation__no_infrastructure__does_nothing(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    deprovision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".deprovision_ingestion_infrastructure",
    )

    # When
    organisation_ingestion_service.disable_ingestion_for_organisation(organisation.id)

    # Then
    deprovision.assert_not_called()


def test_disable_ingestion_for_organisation__errored__deletes_row_without_deprovisioning(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    OrganisationIngestionInfrastructure.objects.create(
        organisation=organisation,
        status=IngestionInfrastructureStatus.ERRORED,
    )
    deprovision = mocker.patch(
        "experimentation.organisation_ingestion_service"
        ".deprovision_ingestion_infrastructure",
    )

    # When
    organisation_ingestion_service.disable_ingestion_for_organisation(organisation.id)

    # Then
    deprovision.assert_not_called()
    assert not OrganisationIngestionInfrastructure.objects.filter(
        organisation=organisation
    ).exists()
