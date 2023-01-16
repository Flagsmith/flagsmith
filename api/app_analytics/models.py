from django.db import models


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4


# TODO: should we store organisation/project?
class APIUsage(models.Model):
    # organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    # project = models.ForeignKey(Project, on_delete=models.CASCADE)

    environment = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=255)
    resource = models.IntegerField(choices=Resource.choices)


class FeatureEvaluation(models.Model):
    feature = models.PositiveIntegerField()
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
