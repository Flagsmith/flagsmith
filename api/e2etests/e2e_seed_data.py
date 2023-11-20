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

    project_test_data = [
        {
            "name": "My Test Project",
            "environments": [
                "Development",
                "Production",
            ],
        },
        {"name": "My Test Project 2", "environments": ["Development"]},
        {"name": "My Test Project 3", "environments": ["Development"]},
        {"name": "My Test Project 4", "environments": ["Development"]},
    ]

    # Create projects and environments
    projects = []
    environments = []
    for project_info in project_test_data:
        project = Project.objects.create(
            name=project_info["name"], organisation=organisation
        )
        projects.append(project)

        for env_name in project_info["environments"]:
            environment = Environment.objects.create(name=env_name, project=project)
            environments.append(environment)

    # Create identities
    identities_test_data = [
        {"identifier": settings.E2E_IDENTITY, "environment": environments[2]},
        {"identifier": settings.E2E_IDENTITY, "environment": environments[3]},
        {"identifier": settings.E2E_IDENTITY, "environment": environments[4]},
    ]

    for identity_info in identities_test_data:
        Identity.objects.create(**identity_info)

    # Upgrade organisation seats
    Subscription.objects.filter(organisation__in=org_admin.organisations.all()).update(
        max_seats=2
    )
