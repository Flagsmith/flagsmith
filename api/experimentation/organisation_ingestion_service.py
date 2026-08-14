from __future__ import annotations

import typing

import structlog

from experimentation.ingestion_infra_service import (
    deprovision_ingestion_infrastructure,
    provision_ingestion_infrastructure,
)
from experimentation.models import (
    IngestionInfrastructureStatus,
    OrganisationIngestionInfrastructure,
)

if typing.TYPE_CHECKING:
    from organisations.models import Organisation

logger = structlog.get_logger("experimentation")


def enable_ingestion_for_organisation(
    organisation: "Organisation",
) -> OrganisationIngestionInfrastructure:
    infrastructure = OrganisationIngestionInfrastructure.objects.filter(
        organisation=organisation
    ).first()
    if (
        infrastructure is not None
        and infrastructure.status == IngestionInfrastructureStatus.CREATED
    ):
        return infrastructure
    if infrastructure is None:
        infrastructure = OrganisationIngestionInfrastructure(organisation=organisation)

    try:
        result = provision_ingestion_infrastructure(organisation.id)
    except Exception as exc:
        infrastructure.status = IngestionInfrastructureStatus.ERRORED
        infrastructure.save()
        logger.error(
            "ingestion_infra.provision_failed",
            exc_info=exc,
            organisation__id=organisation.id,
        )
        raise

    infrastructure.bucket_name = result.bucket_name
    infrastructure.stream_name = result.stream_name
    infrastructure.status = IngestionInfrastructureStatus.CREATED
    infrastructure.save()
    logger.info(
        "ingestion_infra.provisioned",
        organisation__id=organisation.id,
        bucket__name=result.bucket_name,
        stream__name=result.stream_name,
    )
    return infrastructure


def disable_ingestion_for_organisation(organisation_id: int) -> None:
    infrastructure = OrganisationIngestionInfrastructure.objects.filter(
        organisation_id=organisation_id
    ).first()
    if infrastructure is None:
        return

    if infrastructure.status == IngestionInfrastructureStatus.CREATED:
        deprovision_ingestion_infrastructure(organisation_id)
        logger.info(
            "ingestion_infra.torn_down",
            organisation__id=organisation_id,
        )
    infrastructure.delete()
