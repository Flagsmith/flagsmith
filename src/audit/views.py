from rest_framework import viewsets, mixins

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()
