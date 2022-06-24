from core.models import AbstractBaseExportableModel
from django.db import models

from projects.models import Project


class Tag(AbstractBaseExportableModel):
    label = models.CharField(max_length=100)
    color = models.CharField(
        max_length=10, help_text="Hexadecimal value of the tag color"
    )
    description = models.CharField(max_length=512, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    def __str__(self):
        return "Tag %s" % self.label
