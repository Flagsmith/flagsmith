from app.settings.common import (
    E2E_CHANGE_EMAIL_USER,
    E2E_SIGNUP_USER,
    E2E_USER,
)
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole, Subscription
from projects.models import Project
from users.models import FFAdminUser

# Password used by all the test users
PASSWORD = "str0ngp4ssw0rd!"


def delete_user_and_its_organisations(user_email: str) -> None:
    user = FFAdminUser.objects.filter(email=user_email).first()
    if user:
        for organisation in Organisation.objects.filter(
            id__in=user.organisations.all()
        ):
            organisation.delete()
        user.delete()


def teardown() -> None:
    # delete users and their orgs created for e2e test by front end
    delete_user_and_its_organisations(user_email=E2E_SIGNUP_USER)
    delete_user_and_its_organisations(user_email=E2E_USER)
    delete_user_and_its_organisations(user_email=E2E_CHANGE_EMAIL_USER)


def seed_data() -> None:
    # create user and organisation for e2e test by front end
    organisation: Organisation = Organisation.objects.create(name="Bullet Train Ltd")
    org_admin: FFAdminUser = FFAdminUser.objects.create_user(
        email=E2E_USER,
        password=PASSWORD,
        username=E2E_USER,
    )
    org_admin.add_organisation(organisation, OrganisationRole.ADMIN)

    project: Project = Project.objects.create(
        name="My Test Project", organisation=organisation
    )
    Environment.objects.create(name="Development", project=project)
    Environment.objects.create(name="Production", project=project)

    # Upgrade organisation seats
    Subscription.objects.filter(organisation__in=org_admin.organisations.all()).update(
        max_seats=2
    )
