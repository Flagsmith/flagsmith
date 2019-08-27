from rest_framework import viewsets

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ModelViewSet):
    """
    list:
    Get all audit logs within specified environment

    create:
    Create audit log within specified environment

    retrieve:
    Get specific audit log within specified environment
    """

    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
