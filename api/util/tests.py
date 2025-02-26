from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


class Helper:
    def __init__(self):  # type: ignore[no-untyped-def]
        pass

    @staticmethod
    def generate_database_models(identifier="user1"):  # type: ignore[no-untyped-def]
        organisation = Organisation(name="ssg")
        organisation.save()
        project = Project(name="project1", organisation=organisation)
        project.save()
        environment = Environment(name="environment1", project=project)
        environment.save()
        feature = Feature(name="feature1", project=project)
        feature.save()
        identity = Identity(identifier=identifier, environment=environment)
        identity.save()
        return identity, project

    @staticmethod
    def clean_up():  # type: ignore[no-untyped-def]
        Identity.objects.all().delete()
        FeatureState.objects.all().delete()
        Feature.objects.all().delete()
        Environment.objects.all().delete()
        Project.objects.all().delete()
        Organisation.objects.all().delete()

    @staticmethod
    def create_ffadminuser():  # type: ignore[no-untyped-def]
        Helper.clean_up()  # type: ignore[no-untyped-call]
        user = FFAdminUser(
            username="test_user",
            email="test_user@test.com",
            first_name="test",
            last_name="user",
        )
        user.set_password("testuser123")  # type: ignore[no-untyped-call]
        user.save()
        return user
