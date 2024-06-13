from django.conf import settings
from flag_engine.identities.models import IdentityModel as EngineIdentity

from edge_api.identities.models import EdgeIdentity
from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.constants import (
    APPROVE_CHANGE_REQUEST,
    CREATE_CHANGE_REQUEST,
    MANAGE_IDENTITIES,
    MANAGE_SEGMENT_OVERRIDES,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
    VIEW_IDENTITIES,
)
from environments.permissions.models import UserEnvironmentPermission
from organisations.models import Organisation, OrganisationRole, Subscription
from organisations.permissions.models import UserOrganisationPermission
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
)
from projects.models import Project, UserProjectPermission
from projects.permissions import (
    CREATE_ENVIRONMENT,
    CREATE_FEATURE,
    DELETE_FEATURE,
    MANAGE_SEGMENTS,
    VIEW_AUDIT_LOG,
    VIEW_PROJECT,
)
from users.models import FFAdminUser, UserPermissionGroup

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
    delete_user_and_its_organisations(
        user_email=settings.E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS
    )
    delete_user_and_its_organisations(
        user_email=settings.E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS
    )
    delete_user_and_its_organisations(
        user_email=settings.E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS
    )


def seed_data() -> None:
    # create user and organisation for e2e test by front end
    organisation: Organisation = Organisation.objects.create(name="Bullet Train Ltd")
    org_admin: FFAdminUser = FFAdminUser.objects.create_user(
        email=settings.E2E_USER,
        password=PASSWORD,
        username=settings.E2E_USER,
    )
    non_admin_user_with_org_permissions: FFAdminUser = FFAdminUser.objects.create_user(
        email=settings.E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS,
        password=PASSWORD,
        username=settings.E2E_NON_ADMIN_USER_WITH_ORG_PERMISSIONS,
    )
    non_admin_user_with_project_permissions: FFAdminUser = (
        FFAdminUser.objects.create_user(
            email=settings.E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
            password=PASSWORD,
            username=settings.E2E_NON_ADMIN_USER_WITH_PROJECT_PERMISSIONS,
        )
    )
    non_admin_user_with_env_permissions: FFAdminUser = FFAdminUser.objects.create_user(
        email=settings.E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
        password=PASSWORD,
        username=settings.E2E_NON_ADMIN_USER_WITH_ENV_PERMISSIONS,
    )
    org_admin.add_organisation(organisation, OrganisationRole.ADMIN)
    non_admin_user_with_org_permissions.add_organisation(
        organisation,
    )
    non_admin_user_with_project_permissions.add_organisation(
        organisation,
    )
    non_admin_user_with_env_permissions.add_organisation(
        organisation,
    )

    # Add permissions to the non-admin user with org permissions
    user_org_permission = UserOrganisationPermission.objects.create(
        user=non_admin_user_with_org_permissions, organisation=organisation
    )
    user_org_permission.add_permission(CREATE_PROJECT)
    user_org_permission.add_permission(MANAGE_USER_GROUPS)
    UserPermissionGroup.objects.create(name="TestGroup", organisation=organisation)

    # We add different projects and environments to give each e2e test its own isolated context.
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
        {"name": "My Project Permission Project Test", "environments": ["Development"]},
        {"name": "My Env Permission Project Test", "environments": ["Development"]},
    ]
    # Upgrade organisation seats
    Subscription.objects.filter(organisation__in=org_admin.organisations.all()).update(
        max_seats=5, plan="enterprise"
    )

    # Create projects and environments
    projects = []
    environments = []
    for project_info in project_test_data:
        project = Project.objects.create(
            name=project_info["name"], organisation=organisation
        )
        if project_info["name"] == "My Project Permission Project Test":
            # Add permissions to the non-admin user with project permissions
            user_proj_permission: UserProjectPermission = (
                UserProjectPermission.objects.create(
                    user=non_admin_user_with_project_permissions, project=project
                )
            )
            [
                user_proj_permission.add_permission(permission_key)
                for permission_key in [
                    VIEW_PROJECT,
                    CREATE_ENVIRONMENT,
                    MANAGE_SEGMENTS,
                    CREATE_FEATURE,
                    DELETE_FEATURE,
                    VIEW_AUDIT_LOG,
                ]
            ]
        projects.append(project)

        for env_name in project_info["environments"]:
            environment = Environment.objects.create(name=env_name, project=project)

            if project_info["name"] == "My Env Permission Project Test":
                # Add permissions to the non-admin user with env permissions
                user_env_permission = UserEnvironmentPermission.objects.create(
                    user=non_admin_user_with_env_permissions, environment=environment
                )
                [
                    user_env_permission.add_permission(permission_key)
                    for permission_key in [
                        VIEW_ENVIRONMENT,
                        UPDATE_FEATURE_STATE,
                        MANAGE_IDENTITIES,
                        VIEW_IDENTITIES,
                        CREATE_CHANGE_REQUEST,
                        APPROVE_CHANGE_REQUEST,
                        MANAGE_SEGMENT_OVERRIDES,
                    ]
                ]
            environments.append(environment)

    # We're only creating identities for 3 of the 5 environments because
    # they are necessary for the environments created above and to keep
    # the e2e tests isolated."
    identities_test_data = [
        {"identifier": settings.E2E_IDENTITY, "environment": environments[2]},
        {"identifier": settings.E2E_IDENTITY, "environment": environments[3]},
        {"identifier": settings.E2E_IDENTITY, "environment": environments[4]},
    ]

    for identity_info in identities_test_data:
        if settings.IDENTITIES_TABLE_NAME_DYNAMO:
            engine_identity = EngineIdentity(
                identifier=identity_info["identifier"],
                environment_api_key=identity_info["environment"].api_key,
            )
            EdgeIdentity(engine_identity).save()
        else:
            Identity.objects.create(**identity_info)
