from dataclasses import dataclass

from django.conf import settings
from django.db.models import Count

from organisations.models import Organisation
from users.models import FFAdminUser


@dataclass
class TelemetryData:
    organisations: int
    projects: int
    environments: int
    features: int
    segments: int
    users: int

    @property
    def debug_enabled(self):
        return settings.DEBUG

    @property
    def env(self):
        return settings.ENV

    @classmethod
    def generate_telemetry_data(cls) -> "TelemetryData":
        return cls(
            **Organisation.objects.aggregate(
                organisations=Count("id", distinct=True),
                projects=Count("projects", distinct=True),
                environments=Count("projects__environments", distinct=True),
                features=Count("projects__features", distinct=True),
                segments=Count("projects__segments", distinct=True),
            ),
            # users don't _have_ to be associated with an organisation
            users=FFAdminUser.objects.count(),
        )
