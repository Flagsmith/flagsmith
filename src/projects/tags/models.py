from django.db import models

from projects.models import Project


class Tag(models.Model):
    label = models.CharField(max_length=100)
    color = models.CharField(
        max_length=10, help_text="Hexadecimal value of the tag color"
    )
    description = models.CharField(max_length=512)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")

    def __str__(self):
        return "Tag %s" % self.label
