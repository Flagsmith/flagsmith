from django.db import models

from organisations.models import Organisation
from projects.models import Project


class LaunchDarklyImportLogs:
    launch_darkly_import = models.ForeignKey("LaunchDarklyImport")
    log_level = models.CharField()
    log_message = models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)


class LaunchDarklyImport:
    created_by = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    def log(self, log_level, log_message):
        return LaunchDarklyImportLogs.objects.create(
            launch_darkly_import=self, log_level=log_level, log_message=log_message
        )

    def info(self, log_message):
        self.log("INFO", log_message)

    def warning(self, log_message):
        self.log("WARNING", log_message)

    def error(self, log_message):
        self.log("ERROR", log_message)
