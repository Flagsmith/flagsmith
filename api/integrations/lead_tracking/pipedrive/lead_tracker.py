import typing

from integrations.lead_tracking.lead_tracking import LeadTracker
from integrations.lead_tracking.pipedrive.models import PipedriveLead
from users.models import FFAdminUser


class PipedriveLeadTracker(LeadTracker):
    def create_lead(self, user: FFAdminUser):
        return self.client.create_lead(PipedriveLead(title=user.full_name))

    def _get_client(self) -> typing.Any:
        pass
