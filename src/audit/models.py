from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class AuditLog(models.Model):
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    environment = models.ForeignKey(
        'environments.Environment', related_name='audit_logs')
    log = models.TextField()
    author = models.ForeignKey(
        'users.FFAdminUser', related_name='audit_logs', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return "Audit Log %s" % self.id
