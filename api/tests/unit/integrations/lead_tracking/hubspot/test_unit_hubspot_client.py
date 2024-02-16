from integrations.lead_tracking.hubspot.client import create_contact
from users.models import FFAdminUser


def test_hubspot(staff_user: FFAdminUser) -> None:
    create_contact(staff_user)
