from django.conf import settings

from environments.identities.models import Identity
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole, Subscription
from projects.models import Project
from users.models import FFAdminUser

# Password used by all the test users
PASSWORD = "str0ngp4ssw0rd!"


def delete_user_and_its_organisations(user_email: str) -> None:
    user: FFAdminUser | None = FFAdminUser.objects.filter(email=user_email).first()

    if user:
        user.organisations.all().delete()
        user.delete()


def teardown() -> None:
    # delete users and their orgs created for e2e test by front end
    delete_user_and_its_organisations(user_email=settings.E2E_SIGNUP_USER)
    delete_user_and_its_organisations(user_email=settings.E2E_USER)
    delete_user_and_its_organisations(user_email=settings.E2E_CHANGE_EMAIL_USER)


def seed_data() -> None:
    # create user and organisation for e2e test by front end
    organisation: Organisation = Organisation.objects.create(name="Bullet Train Ltd")
    org_admin: FFAdminUser = FFAdminUser.objects.create_user(
        email=settings.E2E_USER,
        password=PASSWORD,
        username=settings.E2E_USER,
    )
    org_admin.add_organisation(organisation, OrganisationRole.ADMIN)

    # Create projects
    project: Project = Project.objects.create(
        name="My Test Project", organisation=organisation
    )
    project2: Project = Project.objects.create(
        name="My Test Project 2", organisation=organisation
    )
    project3: Project = Project.objects.create(
        name="My Test Project 3", organisation=organisation
    )
    project4: Project = Project.objects.create(
        name="My Test Project 4", organisation=organisation
    )
    # Create environments
    TEST_DEV_ENV = "Development"
    Environment.objects.create(name=TEST_DEV_ENV, project=project)
    Environment.objects.create(name="Production", project=project)

    project2_dev_env: Environment = Environment.objects.create(
        name=TEST_DEV_ENV, project=project2
    )
    project3_dev_env: Environment = Environment.objects.create(
        name=TEST_DEV_ENV, project=project3
    )
    project4_dev_env: Environment = Environment.objects.create(
        name=TEST_DEV_ENV, project=project4
    )

    # Create Identities
    Identity.objects.create(
        identifier=settings.E2E_IDENTITY, environment=project2_dev_env
    )

    Identity.objects.create(
        identifier=settings.E2E_IDENTITY, environment=project3_dev_env
    )

    Identity.objects.create(
        identifier=settings.E2E_IDENTITY, environment=project4_dev_env
    )

    # Upgrade organisation seats
    Subscription.objects.filter(organisation__in=org_admin.organisations.all()).update(
        max_seats=2
    )
