from core.models import AbstractBaseExportableModel
from django.db import models

from integrations.launch_darkly.enums import LogLevel
from organisations.models import Organisation
from projects.models import Project


class LaunchDarklyImportLogs(AbstractBaseExportableModel):
    launch_darkly_import = models.ForeignKey(
        "LaunchDarklyImport", on_delete=models.CASCADE
    )
    log_level = models.CharField(max_length=8, choices=LogLevel.choices)
    log_message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class LaunchDarklyImport(AbstractBaseExportableModel):
    created_by = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.CASCADE
    )
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    def log(self, log_level, log_message):
        return LaunchDarklyImportLogs.objects.create(
            launch_darkly_import=self, log_level=log_level, log_message=log_message
        )

    def debug(self, log_message):
        self.log(LogLevel.DEBUG, log_message)

    def info(self, log_message):
        self.log(LogLevel.INFO, log_message)

    def warning(self, log_message):
        self.log(LogLevel.WARNING, log_message)

    def error(self, log_message):
        self.log(LogLevel.ERROR, log_message)

    def critical(self, log_message):
        self.log(LogLevel.CRITICAL, log_message)
