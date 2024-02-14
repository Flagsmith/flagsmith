from core.models import AbstractBaseExportableModel
from django.db import models

from projects.models import Project


class TagType(models.Choices):
    NONE = "NONE"
    STALE = "STALE"


class Tag(AbstractBaseExportableModel):
    label = models.CharField(max_length=100)
    color = models.CharField(
        max_length=10, help_text="Hexadecimal value of the tag color"
    )
    description = models.CharField(max_length=512, blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")

    is_system_tag = models.BooleanField(
        default=False,
        help_text="Indicates that a tag was created by the system, not the user.",
    )
    is_permanent = models.BooleanField(
        default=False,
        help_text="When applied to a feature, it means this feature should be excluded from stale flags logic.",
    )
    type = models.CharField(
        default=TagType.NONE.value,
        choices=TagType.choices,
        help_text="Field used to provide a consistent identifier for the FE and API to use for business logic.",
        max_length=100,
    )

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    def __str__(self):
        return "Tag %s" % self.label
