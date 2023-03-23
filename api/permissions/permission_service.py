from django.db.models import Q

from organisations.models import Organisation, OrganisationRole


def is_user_organisation_admin(user, organisation) -> bool:
    user_organisation = user.get_user_organisation(organisation)
    if user_organisation is not None:
        if user_organisation.role == OrganisationRole.ADMIN.name:
            return True
    return user_is_org_admin_through_role(user, organisation)


def user_is_org_admin_through_role(user, organisation) -> bool:
    user_role_query = Q(roles__userrole__user=user, roles__admin=True)
    group_role_query = Q(roles__grouprole__group__users=user, roles__admin=True)
    query = user_role_query | group_role_query
    query = query & Q(id=organisation.id)
    return Organisation.objects.filter(query).exists()
