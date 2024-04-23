from app_analytics.views import (
    get_usage_data_total_count_view,
    get_usage_data_view,
)
from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from rest_framework_nested import routers

from api_keys.views import MasterAPIKeyViewSet
from audit.views import OrganisationAuditLogViewSet
from integrations.github.views import (
    GithubConfigurationViewSet,
    GithubRepositoryViewSet,
    fetch_issues,
    fetch_pull_requests,
    fetch_repositories,
)
from metadata.views import MetaDataModelFieldViewSet
from organisations.views import (
    OrganisationAPIUsageNotificationView,
    OrganisationWebhookViewSet,
)
from users.views import (
    FFAdminUserViewSet,
    UserPermissionGroupViewSet,
    make_user_group_admin,
    remove_user_as_group_admin,
)

from . import views
from .invites.views import InviteLinkViewSet, InviteViewSet
from .permissions.views import (
    UserOrganisationPermissionViewSet,
    UserPermissionGroupOrganisationPermissionViewSet,
)

router = routers.DefaultRouter()
router.register(r"", views.OrganisationViewSet, basename="organisation")

organisations_router = routers.NestedSimpleRouter(router, r"", lookup="organisation")
organisations_router.register(
    r"invites", InviteViewSet, basename="organisation-invites"
)
organisations_router.register(
    r"metadata-model-fields",
    MetaDataModelFieldViewSet,
    basename="metadata-model-fields",
)
organisations_router.register(
    r"invite-links", InviteLinkViewSet, basename="organisation-invite-links"
)
organisations_router.register(
    r"users", FFAdminUserViewSet, basename="organisation-users"
)
organisations_router.register(
    r"groups", UserPermissionGroupViewSet, basename="organisation-groups"
)
organisations_router.register(
    r"webhooks", OrganisationWebhookViewSet, basename="organisation-webhooks"
)
organisations_router.register(
    r"master-api-keys", MasterAPIKeyViewSet, basename="organisation-master-api-keys"
)
organisations_router.register(
    "user-permissions",
    UserOrganisationPermissionViewSet,
    basename="organisation-user-permission",
)
organisations_router.register(
    "user-group-permissions",
    UserPermissionGroupOrganisationPermissionViewSet,
    basename="organisation-user-group-permission",
)

organisations_router.register(
    "audit", OrganisationAuditLogViewSet, basename="audit-log"
)

organisations_router.register(
    r"integrations/github",
    GithubConfigurationViewSet,
    basename="integrations-github",
)

nested_github_router = routers.NestedSimpleRouter(
    organisations_router, r"integrations/github", lookup="github"
)

nested_github_router.register(
    "repositories",
    GithubRepositoryViewSet,
    basename="repositories",
)

app_name = "organisations"


urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^", include(organisations_router.urls)),
    url(r"^", include(nested_github_router.urls)),
    path(
        "<int:organisation_pk>/usage-data/",
        get_usage_data_view,
        name="usage-data",
    ),
    path(
        "<int:organisation_pk>/usage-data/total-count/",
        get_usage_data_total_count_view,
        name="usage-data-total-count",
    ),
    path(
        "<int:organisation_pk>/groups/<int:group_pk>/users/<int:user_pk>/make-admin",
        make_user_group_admin,
        name="make-user-group-admin",
    ),
    path(
        "<int:organisation_pk>/groups/<int:group_pk>/users/<int:user_pk>/remove-admin",
        remove_user_as_group_admin,
        name="remove-user-group-admin",
    ),
    path(
        "<int:organisation_pk>/github/issues/",
        fetch_issues,
        name="get-github-issues",
    ),
    path(
        "<int:organisation_pk>/github/pulls/",
        fetch_pull_requests,
        name="get-github-pulls",
    ),
    path(
        "<int:organisation_pk>/github/repositories/",
        fetch_repositories,
        name="get-github-installation-repos",
    ),
    path(
        "<int:organisation_pk>/api-usage-notification/",
        OrganisationAPIUsageNotificationView.as_view(),
        name="organisation-api-usage-notification",
    ),
]

if settings.IS_RBAC_INSTALLED:
    from rbac.views import (
        GroupRoleViewSet,
        MasterAPIKeyRoleViewSet,
        RoleEnvironmentPermissionsViewSet,
        RoleOrganisationPermissionViewSet,
        RoleProjectPermissionsViewSet,
        RolesByGroupViewSet,
        RolesbyMasterAPIPrefixViewSet,
        RolesByUserViewSet,
        RoleViewSet,
        UserRoleViewSet,
    )

    organisations_router.register("roles", RoleViewSet, basename="organisation-roles")
    nested_user_roles_routes = routers.NestedSimpleRouter(
        parent_router=organisations_router, parent_prefix=r"users", lookup="user"
    )

    nested_api_key_roles_routes = routers.NestedSimpleRouter(
        parent_router=organisations_router,
        parent_prefix=r"master-api-keys",
        lookup="api_key",
    )

    nested_group_roles_routes = routers.NestedSimpleRouter(
        parent_router=organisations_router, parent_prefix=r"groups", lookup="group"
    )

    nested_roles_router = routers.NestedSimpleRouter(
        organisations_router, r"roles", lookup="role"
    )
    nested_user_roles_routes.register(
        prefix="roles",
        viewset=RolesByUserViewSet,
        basename="role-users",
    )
    nested_api_key_roles_routes.register(
        prefix="roles",
        viewset=RolesbyMasterAPIPrefixViewSet,
        basename="role-api-keys",
    )
    nested_group_roles_routes.register(
        prefix="roles",
        viewset=RolesByGroupViewSet,
        basename="role-groups",
    )
    nested_roles_router.register(
        "environments-permissions",
        RoleEnvironmentPermissionsViewSet,
        basename="roles-environments-permissions",
    )
    nested_roles_router.register(
        "projects-permissions",
        RoleProjectPermissionsViewSet,
        basename="roles-projects-permissions",
    )
    nested_roles_router.register(
        "organisation-permissions",
        RoleOrganisationPermissionViewSet,
        basename="roles-organisations-permissions",
    )
    nested_roles_router.register("groups", GroupRoleViewSet, basename="group-roles")
    nested_roles_router.register("users", UserRoleViewSet, basename="user-roles")
    nested_roles_router.register(
        "master-api-keys", MasterAPIKeyRoleViewSet, basename="master-api-key-roles"
    )
    urlpatterns.extend(
        [
            url(r"^", include(organisations_router.urls)),
            url(r"^", include(nested_roles_router.urls)),
            url(r"^", include(nested_user_roles_routes.urls)),
            url(r"^", include(nested_api_key_roles_routes.urls)),
            url(r"^", include(nested_group_roles_routes.urls)),
        ]
    )
