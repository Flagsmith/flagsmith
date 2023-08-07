from django.db import models


class LaunchDarklyImportLogs():
    launch_darkly_import = models.ForeignKey("LaunchDarklyImport")
    log_level = models.CharField()
    log_message = models.CharField()


class LaunchDarklyImport():
    created_by = models.ForeignKey()
    completed = models.BooleanField(default=False)

    def log(self, log_level, log_message):
        return LaunchDarklyImportLogs.objects.create(
            launch_darkly_import=self,
            log_level=log_level,
            log_message=log_message
        )

    def info(self, log_message):
        self.log("INFO", log_message)

    def warning(self, log_message):
        self.log("WARNING", log_message)

    def error(self, log_message):
        self.log("ERROR", log_message)