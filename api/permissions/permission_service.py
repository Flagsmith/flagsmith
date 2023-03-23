from django.db.models import Q

from organisations.models import Organisation, OrganisationRole
from projects.models import Project


def is_user_organisation_admin(user, organisation: Organisation) -> bool:
    user_organisation = user.get_user_organisation(organisation)
    if user_organisation is not None:
        if user_organisation.role == OrganisationRole.ADMIN.name:
            return True
    return user_is_org_admin_through_role(user, organisation)


def user_is_org_admin_through_role(user, organisation: Organisation) -> bool:
    user_role_query = Q(roles__userrole__user=user, roles__admin=True)
    group_role_query = Q(roles__grouprole__group__users=user, roles__admin=True)

    query = user_role_query | group_role_query

    query = query & Q(id=organisation.id)

    return Organisation.objects.filter(query).exists()


def is_user_project_admin(user, project, allow_org_admin: bool = True) -> bool:
    if allow_org_admin and is_user_organisation_admin(user, project.organisation):
        return True

    user_query = Q(userpermission__user=user, userpermission__admin=True)
    group_query = Q(grouppermission__group__users=user, grouppermission__admin=True)

    user_role_query = Q(
        rolepermission__role__userrole__user=user, rolepermission__admin=True
    )
    groups_role_query = Q(
        rolepermission__role__grouprole__group__users=user,
        rolepermission__admin=True,
    )

    query = user_role_query | groups_role_query | user_query | group_query

    query = query & Q(id=project.id)

    return Project.objects.filter(query).exists()
