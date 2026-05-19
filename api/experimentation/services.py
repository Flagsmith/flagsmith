from __future__ import annotations

import typing

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from experimentation.constants import WAREHOUSE_CONNECTION_FLAG
from integrations.flagsmith.client import get_openfeature_client

if typing.TYPE_CHECKING:
    from experimentation.models import WarehouseConnection
    from organisations.models import Organisation
    from users.models import FFAdminUser


def is_warehouse_feature_enabled(organisation: Organisation) -> bool:
    return get_openfeature_client().get_boolean_value(
        WAREHOUSE_CONNECTION_FLAG,
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def create_warehouse_audit_log(
    connection: WarehouseConnection,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=connection.environment,
        project=connection.environment.project,
        author=user,
        related_object_id=connection.id,
        related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        log=(
            f"Warehouse connection {action} for environment "
            f"{connection.environment.name}"
        ),
    )
