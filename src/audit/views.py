from rest_framework import viewsets, mixins

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer


class AuditLogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        return AuditLog.objects.filter(project__organisation__in=self.request.user.organisations.all())
