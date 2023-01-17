from datetime import date

from django.db import models


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4


class APIUsageRaw(models.Model):
    environment_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=255)
    resource = models.IntegerField(choices=Resource.choices)

    class Meta:
        index_together = (("environment_id", "created_at"),)


class APIUsageAggBucketWindow(models.IntegerChoices):
    HOUR = 1
    DAY = 2


class APIUsageByDay(models.Model):
    environment_id = models.PositiveIntegerField()
    resource = models.IntegerField(choices=Resource.choices)
    total_count = models.PositiveIntegerField()
    date = models.DateField()

    class Meta:
        unique_together = (("environment_id", "resource", "date"),)


class FeatureEvaluation(models.Model):
    feature_id = models.PositiveIntegerField()
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


def aggregate_usage_by_day():
    # let's process for the last bucket first(we might have missed some data)
    last_procssed_bucket = APIUsageByDay.objects.order_by("-date").first()
    if last_procssed_bucket:
        aggregate_for_a_day(last_procssed_bucket.date)
    # now let's process for today
    aggregate_for_a_day(date.today)


def aggregate_for_a_day(day: date):
    data = (
        APIUsageRaw.objects.filter(created_at__gt=day)
        .values("environment_id", "resource")
        .annotate(count=models.Count("id"))
    )
    for row in data:
        APIUsageByDay.objects.update_or_create(
            environment_id=row["environment_id"],
            resource=row["resource"],
            date=day,
            defaults={"total_count": row["count"]},
        )
