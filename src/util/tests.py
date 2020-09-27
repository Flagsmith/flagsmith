from environments.models import Environment
from environments.identities.models import Identity
from features.models import Feature
from features.feature_states.models import FeatureState
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


class Helper:
    def __init__(self):
        pass

    @staticmethod
    def generate_database_models(identifier='user1'):
        organisation = Organisation(name='ssg')
        organisation.save()
        project = Project(name='project1', organisation=organisation)
        project.save()
        environment = Environment(name='environment1', project=project)
        environment.save()
        feature = Feature(name="feature1", project=project)
        feature.save()
        identity = Identity(identifier=identifier, environment=environment)
        identity.save()
        return identity, project

    @staticmethod
    def clean_up():
        Identity.objects.all().delete()
        FeatureState.objects.all().delete()
        Feature.objects.all().delete()
        Environment.objects.all().delete()
        Project.objects.all().delete()
        Organisation.objects.all().delete()

    @staticmethod
    def create_ffadminuser():
        Helper.clean_up()
        user = FFAdminUser(username="test_user", email="test_user@test.com",
                           first_name="test", last_name="user")
        user.set_password("testuser123")
        user.save()
        return user