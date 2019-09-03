from environments.models import Environment, Identity
from projects.models import Project


def get_user_permitted_projects(user):
    user_org_ids = [org.id for org in user.organisations.all()]
    return Project.objects.filter(organisation__in=user_org_ids)


def get_user_permitted_environments(user):
    user_projects = get_user_permitted_projects(user)
    return Environment.objects.filter(project__in=[project.id for project in user_projects.all()])


def get_user_permitted_identities(user):
    user_environments = get_user_permitted_environments(user)
    return Identity.objects.filter(environment__in=[env.id for env in user_environments.all()])


def get_environment_from_request(request):
    try:
        return Environment.objects.get(api_key=request.META.get('HTTP_X_ENVIRONMENT_KEY'))
    except Environment.DoesNotExist:
        return None
