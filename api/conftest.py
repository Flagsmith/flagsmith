import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import EQUAL, Condition, Segment, SegmentRule
from users.models import FFAdminUser

trait_key = "key1"
trait_value = "value1"


@pytest.fixture()
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture()
def organisation(db, admin_user):
    org = Organisation.objects.create(name="Test Org")
    admin_user.add_organisation(org, role=OrganisationRole.ADMIN)
    return org


@pytest.fixture()
def project(organisation):
    return Project.objects.create(name="Test Project", organisation=organisation)


@pytest.fixture()
def environment(project):
    return Environment.objects.create(name="Test Environment", project=project)


@pytest.fixture()
def identity(environment):
    return Identity.objects.create(identifier="test_identity", environment=environment)


@pytest.fixture()
def trait(identity):
    return Trait.objects.create(
        identity=identity, trait_key=trait_key, string_value=trait_value
    )


@pytest.fixture()
def multivariate_feature(project):
    feature = Feature.objects.create(
        name="feature", project=project, type=MULTIVARIATE, initial_value="control"
    )

    for percentage_allocation in (30, 30, 40):
        string_value = f"multivariate option for {percentage_allocation}% of users."
        MultivariateFeatureOption.objects.create(
            feature=feature,
            default_percentage_allocation=percentage_allocation,
            type=STRING,
            string_value=string_value,
        )

    return feature


@pytest.fixture()
def identity_matching_segment(project, trait):
    segment = Segment.objects.create(name="Matching segment", project=project)
    matching_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        rule=matching_rule,
        property=trait.trait_key,
        operator=EQUAL,
        value=trait.trait_value,
    )
    return segment


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def feature(project, environment):
    return Feature.objects.create(name="Test Feature1", project=project)


@pytest.fixture()
def user_password():
    return FFAdminUser.objects.make_random_password()


@pytest.fixture()
def reset_cache():
    cache.clear()
    yield
    cache.clear()
