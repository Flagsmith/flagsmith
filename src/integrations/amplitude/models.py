from django.db import models

from environments.models import Environment


class AmplitudeConfiguration(models.Model):
    api_key = models.CharField(max_length=100, blank=False, null=False)
    environment = models.OneToOneField(Environment, related_name='amplitude_config', on_delete=models.CASCADE)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
