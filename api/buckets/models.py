from django.core.exceptions import ValidationError
from django.db import models

from audit.related_object_type import RelatedObjectType
from core.models import (
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from projects.models import Project


class Bucket(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    """
    Bucket entity for grouping Features within a Project.

    Buckets provide a way to organize features into logical groups.
    Each bucket belongs to a single project, and features can optionally
    belong to one bucket.
    """

    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)

    project = models.ForeignKey(
        Project,
        related_name="buckets",
        on_delete=models.CASCADE,
    )

    history_record_class_path = "buckets.models.HistoricalBucket"
    related_object_type = RelatedObjectType.BUCKET

    class Meta:
        ordering = ("id",)
        constraints = [
            models.UniqueConstraint(
                fields=["project", "name"], name="unique_bucket_name_per_project"
            )
        ]

    def __str__(self):
        return f"Bucket {self.name} - Project {self.project.name}"

    def validate_unique(self, *args, **kwargs):
        """
        Checks unique constraints on the model and raises ValidationError if any failed.
        Enforces case-insensitive name check per project.
        """
        super().validate_unique(*args, **kwargs)

        if (
            Bucket.objects.filter(project=self.project, name__iexact=self.name)
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                {
                    "name": [
                        "Bucket with that name already exists for this project. "
                        "Note that bucket names are case insensitive.",
                    ],
                }
            )

    def get_create_log_message(self, history_instance):
        return f"Bucket {self.name} created"

    def get_delete_log_message(self, history_instance):
        return f"Bucket {self.name} deleted"

    def get_update_log_message(self, history_instance):
        return f"Bucket {self.name} updated"

    def _get_project(self):
        return self.project
