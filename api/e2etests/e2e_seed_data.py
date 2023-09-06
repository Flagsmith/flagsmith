from app.settings.common import (
    E2E_CHANGE_EMAIL_USER,
    E2E_SIGNUP_USER,
    E2E_USER,
)
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole, Subscription
from projects.models import Project
from users.models import FFAdminUser


class E2ESeedData:
    def __init__(self) -> None:
        # User email address used for E2E Signup test
        self.signup_user: str = E2E_SIGNUP_USER

        # User email address used for Change email E2E test which is part of invite tests
        self.change_email_user: str = E2E_CHANGE_EMAIL_USER

        # User email address used for the rest of the E2E tests
        self.e2e_user: str = E2E_USER

        # Password used by all the test users
        self.password = "str0ngp4ssw0rd!"

    def teardown(self) -> None:
        # delete users created for e2e test by front end
        FFAdminUser.objects.filter(email=self.signup_user).delete()
        FFAdminUser.objects.filter(email=self.e2e_user).delete()
        FFAdminUser.objects.filter(email=self.change_email_user).delete()

    def seed_data(self) -> None:
        # create user and organisation for e2e test by front end
        organisation: Organisation = Organisation.objects.create(
            name="Bullet Train Ltd"
        )
        org_admin: FFAdminUser = FFAdminUser.objects.create_user(
            email=self.e2e_user,
            password=self.password,
            username=self.e2e_user,
        )
        org_admin.add_organisation(organisation, OrganisationRole.ADMIN)

        project: Project = Project.objects.create(
            name="My Test Project", organisation=organisation
        )
        Environment.objects.create(name="Development", project=project)
        Environment.objects.create(name="Production", project=project)

        # Upgrade organisation seats
        Subscription.objects.filter(
            organisation__in=org_admin.organisations.all()
        ).update(max_seats=2)
