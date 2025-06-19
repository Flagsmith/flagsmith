import logging
import os
import site
import typing
from unittest.mock import MagicMock

import boto3
import pytest
from common.environments.permissions import (
    MANAGE_IDENTITIES,
    MANAGE_SEGMENT_OVERRIDES,
    VIEW_ENVIRONMENT,
    VIEW_IDENTITIES,
)
from common.projects.permissions import VIEW_PROJECT
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.signals import (
    register_type_handlers,
)
from django.core.cache import caches
from django.db.backends.base.creation import TEST_DATABASE_PREFIX
from django.test.utils import setup_databases
from flag_engine.segments.constants import EQUAL
from moto import mock_dynamodb  # type: ignore[import-untyped]
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest import FixtureRequest
from pytest_django import DjangoDbBlocker
from pytest_django.fixtures import SettingsWrapper
from pytest_django.plugin import blocking_manager_key
from pytest_mock import MockerFixture
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from task_processor.task_run_method import TaskRunMethod
from urllib3 import BaseHTTPResponse
from urllib3.connectionpool import HTTPConnectionPool
from xdist import get_xdist_worker_id  # type: ignore[import-untyped]

from api_keys.models import MasterAPIKey
from api_keys.user import APIKeyUser
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment, EnvironmentAPIKey
from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from features.feature_external_resources.models import FeatureExternalResource
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import STRING
from features.versioning.tasks import enable_v2_versioning
from features.workflows.core.models import ChangeRequest
from integrations.github.models import GithubConfiguration, GitHubRepository
from metadata.models import (
    Metadata,
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from organisations.models import Organisation, OrganisationRole, Subscription
from organisations.permissions.models import (
    OrganisationPermissionModel,
    UserOrganisationPermission,
)
from organisations.permissions.permissions import (
    CREATE_PROJECT,
    MANAGE_USER_GROUPS,
)
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_ID,
    SCALE_UP,
    STARTUP,
    XERO,
)
from permissions.models import PermissionModel
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule
from segments.services import SegmentCloneService
from tests.test_helpers import fix_issue_3869
from tests.types import (
    AdminClientAuthType,
    WithEnvironmentPermissionsCallable,
    WithOrganisationPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser, UserPermissionGroup


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ci",
        action="store_true",
        default=False,
        help="Enable CI mode",
    )


def pytest_sessionstart(session: pytest.Session) -> None:
    fix_issue_3869()  # type: ignore[no-untyped-call]


@pytest.fixture()
def post_request_mock(mocker: MockerFixture) -> MagicMock:
    def mocked_request(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        class MockResponse:
            def __init__(self, json_data: str, status_code: int) -> None:
                self.json_data = json_data
                self.status_code = status_code

            def raise_for_status(self) -> None:
                pass

            def json(self) -> str:
                return self.json_data

        return MockResponse(json_data={"data": "data"}, status_code=200)  # type: ignore[arg-type,return-value]

    return mocker.patch("requests.post", side_effect=mocked_request)


@pytest.hookimpl(trylast=True)  # type: ignore[misc]
def pytest_configure(config: pytest.Config) -> None:
    if (
        config.option.ci
        and config.option.dist != "no"
        and not hasattr(config, "workerinput")
    ):
        with config.stash[blocking_manager_key].unblock():
            setup_databases(
                verbosity=config.option.verbose,
                interactive=False,
                parallel=config.option.numprocesses,
            )


@pytest.fixture
def fs(fs: FakeFilesystem) -> FakeFilesystem:
    """
    Provide a fake filesystem for tests

    NOTE: Sometimes pyfakefs patching goes wonky, causing the fake file system
    to be cached across tests. This can lead tests failing to access real files
    even if they do not use this fixture. Because we can't fix this issue now,
    it's safer to allow site-packages [read-only] access from tests.
    """
    app_path = os.path.dirname(os.path.abspath(__file__))
    site_packages = site.getsitepackages()  # Allow files within dependencies
    paths_to_add = [app_path]
    for site_package_path in site_packages:
        if not site_package_path.startswith(app_path):
            paths_to_add.append(site_package_path)
    fs.add_real_paths(paths_to_add)
    return fs


@pytest.fixture(scope="session")
def django_db_setup(
    request: pytest.FixtureRequest,
    django_db_blocker: DjangoDbBlocker,
) -> None:
    if (
        request.config.option.ci
        # xdist worker id is either `gw[0-9]+` or `master`
        and (xdist_worker_id_suffix := get_xdist_worker_id(request)[2:]).isnumeric()
    ):
        # Django's test database clone indices start at 1,
        # Pytest's worker indices are 0-based
        test_db_suffix = str(int(xdist_worker_id_suffix) + 1)
    else:
        # Tests are run on main node, which assumes -n0
        return request.getfixturevalue("django_db_setup")  # type: ignore[no-any-return] # pragma: no cover

    from django.conf import settings

    for db_settings in settings.DATABASES.values():
        test_db_name = f"{TEST_DATABASE_PREFIX}{db_settings['NAME']}_{test_db_suffix}"
        db_settings["NAME"] = test_db_name

    from django.db import connections

    if request.config.option.ci:
        # Ensure psycopg type handlers are registered.
        # This is necessary for tests that involve `HStoreField`.
        for connection in connections.all():
            if connection.vendor == "postgresql":
                with django_db_blocker.unblock():
                    register_type_handlers(connection)


@pytest.fixture(autouse=True)
def restrict_http_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    This fixture prevents all tests from performing HTTP requests to
    any host than `localhost`.

    Any external request attempt leads to `RuntimeError` with a helpful message
    pointing developers to the `responses` fixture.
    """
    allowed_hosts = {"localhost"}
    original_urlopen = HTTPConnectionPool.urlopen

    def urlopen_mock(  # type: ignore[no-untyped-def]
        self,
        method: str,
        url: str,
        *args,
        **kwargs,
    ) -> BaseHTTPResponse:
        if self.host in allowed_hosts:
            return original_urlopen(self, method, url, *args, **kwargs)

        raise RuntimeError(
            f"Blocked {method} request to {self.scheme}://{self.host}{url}. "
            "Use `responses` fixture to mock the response!"
        )

    monkeypatch.setattr(
        "urllib3.connectionpool.HTTPConnectionPool.urlopen", urlopen_mock
    )


trait_key = "key1"
trait_value = "value1"


@pytest.fixture()
def test_user(django_user_model):  # type: ignore[no-untyped-def]
    return django_user_model.objects.create(email="user@example.com")


@pytest.fixture()
def auth_token(test_user):  # type: ignore[no-untyped-def]
    return Token.objects.create(user=test_user)


@pytest.fixture()
def admin_client_original(admin_user):  # type: ignore[no-untyped-def]
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture()
def admin_client(admin_client_original):  # type: ignore[no-untyped-def]
    """
    This fixture will eventually be switched over to what is now
    called admin_client_new which will run an admin client as well
    as admin_master_api_key_client automatically.

    In the meantime consider this fixture as deprecated. Use either
    admin_client_original to preserve a singular admin client or
    if the test suite can handle it, use admin_client_new to
    automatically handling both query methods.

    If a test must use pytest.mark.parametrize to differentiate
    between other required parameters for a test then please
    use admin_client_original as the parametrized version as this
    fixture will ultimately be updated to the new approach.
    """
    yield admin_client_original


@pytest.fixture()
def test_user_client(api_client, test_user):  # type: ignore[no-untyped-def]
    api_client.force_authenticate(test_user)
    return api_client


@pytest.fixture()
def staff_user(django_user_model):  # type: ignore[no-untyped-def]
    """
    A non-admin user fixture.

    To add to an environment with permissions use the fixture
    with_environment_permissions, or similar with the fixture


    This fixture is attached to the organisation fixture.
    """
    return django_user_model.objects.create(email="staff@example.com")


@pytest.fixture()
def staff_client(staff_user):  # type: ignore[no-untyped-def]
    client = APIClient()
    client.force_authenticate(user=staff_user)
    return client


@pytest.fixture()
def organisation(db, admin_user, staff_user):  # type: ignore[no-untyped-def]
    org = Organisation.objects.create(name="Test Org")
    admin_user.add_organisation(org, role=OrganisationRole.ADMIN)
    staff_user.add_organisation(org, role=OrganisationRole.USER)
    return org


@pytest.fixture()
def default_user_permission_group(organisation):  # type: ignore[no-untyped-def]
    return UserPermissionGroup.objects.create(
        organisation=organisation, name="Default user permission group", is_default=True
    )


@pytest.fixture()
def user_permission_group(organisation, admin_user):  # type: ignore[no-untyped-def]
    user_permission_group = UserPermissionGroup.objects.create(
        organisation=organisation, name="User permission group", is_default=False
    )
    user_permission_group.users.add(admin_user)
    return user_permission_group


@pytest.fixture()
def subscription(organisation):  # type: ignore[no-untyped-def]
    subscription = Subscription.objects.get(organisation=organisation)
    # refresh organisation to load subscription
    organisation.refresh_from_db()
    return subscription


@pytest.fixture()
def xero_subscription(organisation):  # type: ignore[no-untyped-def]
    subscription = Subscription.objects.get(organisation=organisation)
    subscription.payment_method = XERO
    subscription.subscription_id = "subscription-id"
    subscription.save()

    # refresh organisation to load subscription
    organisation.refresh_from_db()
    return subscription


@pytest.fixture()
def chargebee_subscription(organisation: Organisation) -> Subscription:
    subscription = Subscription.objects.get(organisation=organisation)
    subscription.payment_method = CHARGEBEE
    subscription.subscription_id = "subscription-id"
    subscription.plan = "scale-up-v2"
    subscription.save()

    # refresh organisation to load subscription
    organisation.refresh_from_db()
    return subscription  # type: ignore[no-any-return]


@pytest.fixture()
def tag(project):  # type: ignore[no-untyped-def]
    return Tag.objects.create(label="tag", project=project, color="#000000")


@pytest.fixture()
def system_tag(project: Project) -> Tag:
    return Tag.objects.create(  # type: ignore[no-any-return]
        label="system-tag", project=project, color="#FFFFFF", is_system_tag=True
    )


@pytest.fixture()
def enterprise_subscription(organisation: Organisation) -> Subscription:
    Subscription.objects.filter(organisation=organisation).update(
        plan="enterprise", subscription_id="subscription-id"
    )
    organisation.refresh_from_db()
    return organisation.subscription


@pytest.fixture()
def startup_subscription(organisation: Organisation) -> Subscription:
    Subscription.objects.filter(organisation=organisation).update(
        plan=STARTUP, subscription_id="subscription-id"
    )
    organisation.refresh_from_db()
    return organisation.subscription


@pytest.fixture()
def scale_up_subscription(organisation: Organisation) -> Subscription:
    Subscription.objects.filter(organisation=organisation).update(
        plan=SCALE_UP, subscription_id="subscription-id"
    )
    organisation.refresh_from_db()
    return organisation.subscription


@pytest.fixture()
def free_subscription(organisation: Organisation) -> Subscription:
    Subscription.objects.filter(organisation=organisation).update(
        plan=FREE_PLAN_ID, subscription_id="subscription-id"
    )
    organisation.refresh_from_db()
    return organisation.subscription


@pytest.fixture()
def project(organisation):  # type: ignore[no-untyped-def]
    return Project.objects.create(name="Test Project", organisation=organisation)


@pytest.fixture()
def segment(project: Project):  # type: ignore[no-untyped-def]
    _segment = Segment.objects.create(name="segment", project=project)
    # Deep clone the segment to ensure that any bugs around
    # versioning get bubbled up through the test suite.
    SegmentCloneService(_segment).deep_clone()

    return _segment


@pytest.fixture()
def another_segment(project: Project) -> Segment:
    return Segment.objects.create(name="another_segment", project=project)  # type: ignore[no-any-return]


@pytest.fixture()
def segment_rule(segment):  # type: ignore[no-untyped-def]
    return SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)


@pytest.fixture()
def feature_specific_segment(feature: Feature) -> Segment:
    return Segment.objects.create(  # type: ignore[no-any-return]
        feature=feature, name="feature specific segment", project=feature.project
    )


@pytest.fixture()
def environment(project):  # type: ignore[no-untyped-def]
    return Environment.objects.create(name="Test Environment", project=project)


@pytest.fixture()
def with_environment_permissions(
    environment: Environment, staff_user: FFAdminUser
) -> WithEnvironmentPermissionsCallable:
    """
    Add environment permissions to the staff_user fixture.
    Defaults to associating to the environment fixture.
    """

    def _with_environment_permissions(
        permission_keys: list[str] | None = None,
        environment_id: int | None = None,
        admin: bool = False,
    ) -> UserEnvironmentPermission:
        environment_id = environment_id or environment.id
        uep, __ = UserEnvironmentPermission.objects.get_or_create(
            environment_id=environment_id, user=staff_user, defaults={"admin": admin}
        )
        if permission_keys:
            uep.permissions.add(*permission_keys)  # type: ignore[arg-type]

        return uep

    return _with_environment_permissions


@pytest.fixture()
def with_organisation_permissions(
    organisation: Organisation, staff_user: FFAdminUser
) -> WithOrganisationPermissionsCallable:
    """
    Add organisation permissions to the staff_user fixture.
    Defaults to associating to the organisation fixture.
    """

    def _with_organisation_permissions(
        permission_keys: list[str], organisation_id: int | None = None
    ) -> UserOrganisationPermission:
        organisation_id = organisation_id or organisation.id
        uop, __ = UserOrganisationPermission.objects.get_or_create(
            organisation_id=organisation_id, user=staff_user
        )
        uop.permissions.add(*permission_keys)  # type: ignore[arg-type]

        return uop

    return _with_organisation_permissions


@pytest.fixture()
def with_project_permissions(
    project: Project, staff_user: FFAdminUser
) -> WithProjectPermissionsCallable:
    """
    Add project permissions to the staff_user fixture.
    Defaults to associating to the project fixture.
    """

    def _with_project_permissions(
        permission_keys: list[str] | None = None,
        project_id: typing.Optional[int] = None,
        admin: bool = False,
    ) -> UserProjectPermission:
        project_id = project_id or project.id
        upp, __ = UserProjectPermission.objects.get_or_create(
            project_id=project_id, user=staff_user, admin=admin
        )

        if permission_keys:
            upp.permissions.add(*permission_keys)  # type: ignore[arg-type]

        return upp

    return _with_project_permissions


@pytest.fixture()
def environment_v2_versioning(environment: Environment) -> Environment:
    enable_v2_versioning(environment.id)
    environment.refresh_from_db()
    return environment


@pytest.fixture()
def identity(environment: Environment) -> Identity:
    return Identity.objects.create(identifier="test_identity", environment=environment)


@pytest.fixture()
def identity_featurestate(identity, feature):  # type: ignore[no-untyped-def]
    return FeatureState.objects.create(
        identity=identity, feature=feature, environment=identity.environment
    )


@pytest.fixture()
def trait(identity):  # type: ignore[no-untyped-def]
    return Trait.objects.create(
        identity=identity, trait_key=trait_key, string_value=trait_value
    )


@pytest.fixture()
def multivariate_feature(project):  # type: ignore[no-untyped-def]
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
def multivariate_options(
    multivariate_feature: Feature,
) -> list[MultivariateFeatureOption]:
    return list(multivariate_feature.multivariate_options.all())


@pytest.fixture()
def identity_matching_segment(project: Project, trait: Trait) -> Segment:
    segment: Segment = Segment.objects.create(name="Matching segment", project=project)
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
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture()
def feature(project: Project) -> Feature:
    return Feature.objects.create(name="Test Feature1", project=project)  # type: ignore[no-any-return]


@pytest.fixture()
def change_request(environment: Environment, admin_user: FFAdminUser) -> ChangeRequest:
    return ChangeRequest.objects.create(  # type: ignore[no-any-return]
        environment=environment, title="Test CR", user_id=admin_user.id
    )


@pytest.fixture()
def project_change_request(project: Project, admin_user: FFAdminUser) -> ChangeRequest:
    return ChangeRequest.objects.create(  # type: ignore[no-any-return]
        project=project, title="Test Project CR", user_id=admin_user.id
    )


@pytest.fixture()
def feature_state(feature: Feature, environment: Environment) -> FeatureState:
    return FeatureState.objects.get(environment=environment, feature=feature)  # type: ignore[no-any-return]


@pytest.fixture()
def feature_state_with_value(
    environment: Environment, request: FixtureRequest
) -> FeatureState:
    initial_value = getattr(request, "param", "foo")
    feature = Feature.objects.create(
        name="feature_with_value",
        initial_value=initial_value,
        default_enabled=True,
        project=environment.project,
    )
    return FeatureState.objects.get(  # type: ignore[no-any-return]
        environment=environment, feature=feature, feature_segment=None, identity=None
    )


@pytest.fixture()
def feature_with_value(project: Project, environment: Environment) -> Feature:
    return Feature.objects.create(  # type: ignore[no-any-return]
        name="feature_with_value",
        initial_value="value",
        default_enabled=False,
        project=environment.project,
    )


@pytest.fixture()
def change_request_feature_state(feature, environment, change_request, feature_state):  # type: ignore[no-untyped-def]
    feature_state.change_request = change_request
    feature_state.save()
    return feature_state


@pytest.fixture()
def feature_based_segment(project, feature):  # type: ignore[no-untyped-def]
    return Segment.objects.create(name="segment", project=project, feature=feature)


@pytest.fixture()
def user_password():  # type: ignore[no-untyped-def]
    return FFAdminUser.objects.make_random_password()


@pytest.fixture()
def reset_cache():  # type: ignore[no-untyped-def]
    # https://groups.google.com/g/django-developers/c/zlaPsP13dUY
    # TL;DR: Use this if your test interacts with cache since django
    # does not clear cache after every test
    # Clear all caches before the test
    for cache in caches.all():
        cache.clear()

    yield

    # Clear all caches after the test
    for cache in caches.all():
        cache.clear()


@pytest.fixture()
def feature_segment(feature, segment, environment):  # type: ignore[no-untyped-def]
    return FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )


@pytest.fixture()
def segment_featurestate(feature_segment, feature, environment):  # type: ignore[no-untyped-def]
    return FeatureState.objects.create(
        feature_segment=feature_segment, feature=feature, environment=environment
    )


@pytest.fixture()
def another_segment_featurestate(
    feature: Feature, environment: Environment, another_segment: Segment
) -> FeatureState:
    return FeatureState.objects.create(  # type: ignore[no-any-return]
        feature_segment=FeatureSegment.objects.create(
            feature=feature, segment=another_segment, environment=environment
        ),
        feature=feature,
        environment=environment,
    )


@pytest.fixture()
def feature_with_value_segment(
    feature_with_value: Feature, segment: Segment, environment: Environment
) -> FeatureSegment:
    return FeatureSegment.objects.create(  # type: ignore[no-any-return]
        feature=feature_with_value, segment=segment, environment=environment
    )


@pytest.fixture()
def segment_override_for_feature_with_value(
    feature_with_value_segment: FeatureSegment,
    feature_with_value: Feature,
    environment: Environment,
) -> FeatureState:
    return FeatureState.objects.create(  # type: ignore[no-any-return]
        feature_segment=feature_with_value_segment,
        feature=feature_with_value,
        environment=environment,
        updated_at="2024-01-01 00:00:00",
    )


@pytest.fixture()
def environment_api_key(environment):  # type: ignore[no-untyped-def]
    return EnvironmentAPIKey.objects.create(
        environment=environment, name="Test API Key"
    )


@pytest.fixture()
def master_api_key_name() -> str:
    return "test-key"


@pytest.fixture()
def admin_master_api_key(organisation: Organisation) -> typing.Tuple[MasterAPIKey, str]:
    master_api_key, key = MasterAPIKey.objects.create_key(
        name="test_key", organisation=organisation, is_admin=True
    )
    return master_api_key, key  # type: ignore[return-value]


@pytest.fixture()
def master_api_key(
    master_api_key_name: str, organisation: Organisation
) -> typing.Tuple[MasterAPIKey, str]:
    master_api_key, key = MasterAPIKey.objects.create_key(
        name=master_api_key_name, organisation=organisation, is_admin=False
    )
    return master_api_key, key  # type: ignore[return-value]


@pytest.fixture()
def admin_user_email(admin_user: FFAdminUser) -> str:
    return admin_user.email


@pytest.fixture
def master_api_key_object(
    master_api_key: typing.Tuple[MasterAPIKey, str],
) -> MasterAPIKey:
    return master_api_key[0]


@pytest.fixture
def master_api_key_id(master_api_key_object: MasterAPIKey) -> str:
    return master_api_key_object.id


@pytest.fixture
def admin_user_id(admin_user: FFAdminUser) -> str:
    return admin_user.id  # type: ignore[return-value]


@pytest.fixture
def admin_master_api_key_object(
    admin_master_api_key: typing.Tuple[MasterAPIKey, str],
) -> MasterAPIKey:
    return admin_master_api_key[0]


@pytest.fixture
def api_key_user(master_api_key_object: MasterAPIKey) -> APIKeyUser:
    return APIKeyUser(master_api_key_object)


@pytest.fixture()
def admin_master_api_key_client(
    admin_master_api_key: typing.Tuple[MasterAPIKey, str],
) -> APIClient:
    key = admin_master_api_key[1]
    # Can not use `api_client` fixture here because:
    # https://docs.pytest.org/en/6.2.x/fixture.html#fixtures-can-be-requested-more-than-once-per-test-return-values-are-cached
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Api-Key " + key)
    return api_client


@pytest.fixture()
def view_environment_permission(db):  # type: ignore[no-untyped-def]
    return PermissionModel.objects.get(key=VIEW_ENVIRONMENT)


@pytest.fixture()
def manage_identities_permission(db):  # type: ignore[no-untyped-def]
    return PermissionModel.objects.get(key=MANAGE_IDENTITIES)


@pytest.fixture()
def view_identities_permission(db):  # type: ignore[no-untyped-def]
    return PermissionModel.objects.get(key=VIEW_IDENTITIES)


@pytest.fixture()
def view_project_permission(db):  # type: ignore[no-untyped-def]
    return PermissionModel.objects.get(key=VIEW_PROJECT)


@pytest.fixture()
def create_project_permission(db):  # type: ignore[no-untyped-def]
    return PermissionModel.objects.get(key=CREATE_PROJECT)


@pytest.fixture()
def manage_segment_overrides_permission(db: None) -> PermissionModel:
    return PermissionModel.objects.get(key=MANAGE_SEGMENT_OVERRIDES)


@pytest.fixture()
def user_environment_permission(test_user, environment):  # type: ignore[no-untyped-def]
    return UserEnvironmentPermission.objects.create(
        user=test_user, environment=environment
    )


@pytest.fixture()
def user_environment_permission_group(test_user, user_permission_group, environment):  # type: ignore[no-untyped-def]
    return UserPermissionGroupEnvironmentPermission.objects.create(
        group=user_permission_group, environment=environment
    )


@pytest.fixture()
def user_project_permission(test_user, project):  # type: ignore[no-untyped-def]
    return UserProjectPermission.objects.create(user=test_user, project=project)


@pytest.fixture()
def user_project_permission_group(project, user_permission_group):  # type: ignore[no-untyped-def]
    return UserPermissionGroupProjectPermission.objects.create(
        group=user_permission_group, project=project
    )


@pytest.fixture(autouse=True)
def task_processor_synchronously(settings):  # type: ignore[no-untyped-def]
    settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY


@pytest.fixture()
def a_metadata_field(organisation: Organisation) -> MetadataField:
    return MetadataField.objects.create(name="a", type="int", organisation=organisation)  # type: ignore[no-any-return]  # noqa: E501


@pytest.fixture()
def b_metadata_field(organisation: Organisation) -> MetadataField:
    return MetadataField.objects.create(name="b", type="str", organisation=organisation)  # type: ignore[no-any-return]  # noqa: E501


@pytest.fixture()
def required_a_environment_metadata_field(
    organisation: Organisation,
    a_metadata_field: MetadataField,
    environment: Environment,
    project: Project,
    project_content_type: ContentType,
) -> MetadataModelField:
    environment_type = ContentType.objects.get_for_model(environment)
    model_field = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=environment_type,
    )

    MetadataModelFieldRequirement.objects.create(
        content_type=project_content_type, object_id=project.id, model_field=model_field
    )
    return model_field  # type: ignore[no-any-return]


@pytest.fixture()
def required_a_feature_metadata_field(
    organisation: Organisation,
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    project: Project,
    project_content_type: ContentType,
) -> MetadataModelField:
    model_field = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=feature_content_type,
    )

    MetadataModelFieldRequirement.objects.create(
        content_type=project_content_type, object_id=project.id, model_field=model_field
    )

    return model_field  # type: ignore[no-any-return]


@pytest.fixture()
def required_a_feature_metadata_field_using_organisation_content_type(
    organisation: Organisation,
    a_metadata_field: MetadataField,
    feature_content_type: ContentType,
    project: Project,
    organisation_content_type: ContentType,
) -> MetadataModelField:
    model_field = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=feature_content_type,
    )

    MetadataModelFieldRequirement.objects.create(
        content_type=organisation_content_type,
        object_id=organisation.id,
        model_field=model_field,
    )

    return model_field  # type: ignore[no-any-return]


@pytest.fixture()
def required_a_segment_metadata_field(
    organisation: Organisation,
    a_metadata_field: MetadataField,
    segment_content_type: ContentType,
    project: Project,
    project_content_type: ContentType,
) -> MetadataModelField:
    model_field = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=segment_content_type,
    )

    MetadataModelFieldRequirement.objects.create(
        content_type=project_content_type, object_id=project.id, model_field=model_field
    )

    return model_field  # type: ignore[no-any-return]


@pytest.fixture()
def required_a_segment_metadata_field_using_organisation_content_type(
    organisation: Organisation,
    a_metadata_field: MetadataField,
    segment_content_type: ContentType,
    project: Project,
    organisation_content_type: ContentType,
) -> MetadataModelField:
    model_field = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=segment_content_type,
    )

    MetadataModelFieldRequirement.objects.create(
        content_type=organisation_content_type,
        object_id=organisation.id,
        model_field=model_field,
    )

    return model_field  # type: ignore[no-any-return]


@pytest.fixture()
def optional_b_feature_metadata_field(
    organisation: Organisation, b_metadata_field: MetadataField, feature: Feature
) -> MetadataModelField:
    feature_type = ContentType.objects.get_for_model(feature)

    return MetadataModelField.objects.create(  # type: ignore[no-any-return]
        field=b_metadata_field,
        content_type=feature_type,
    )


@pytest.fixture()
def optional_b_segment_metadata_field(
    organisation: Organisation, b_metadata_field: MetadataField, segment: Segment
) -> MetadataModelField:
    segment_type = ContentType.objects.get_for_model(segment)

    return MetadataModelField.objects.create(  # type: ignore[no-any-return]
        field=b_metadata_field,
        content_type=segment_type,
    )


@pytest.fixture()
def optional_b_environment_metadata_field(
    organisation: Organisation,
    b_metadata_field: MetadataField,
    environment: Environment,
) -> MetadataModelField:
    environment_type = ContentType.objects.get_for_model(environment)

    return MetadataModelField.objects.create(  # type: ignore[no-any-return]
        field=b_metadata_field,
        content_type=environment_type,
    )


@pytest.fixture()
def environment_metadata_a(
    environment: Environment,
    required_a_environment_metadata_field: MetadataModelField,
) -> Metadata:
    environment_type = ContentType.objects.get_for_model(environment)
    return Metadata.objects.create(  # type: ignore[no-any-return]
        object_id=environment.id,
        content_type=environment_type,
        model_field=required_a_environment_metadata_field,
        field_value="10",
    )


@pytest.fixture()
def environment_metadata_b(
    environment: Environment,
    optional_b_environment_metadata_field: MetadataModelField,
) -> Metadata:
    environment_type = ContentType.objects.get_for_model(environment)
    return Metadata.objects.create(  # type: ignore[no-any-return]
        object_id=environment.id,
        content_type=environment_type,
        model_field=optional_b_environment_metadata_field,
        field_value="10",
    )


@pytest.fixture()
def environment_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Environment)


@pytest.fixture()
def feature_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Feature)


@pytest.fixture()
def segment_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Segment)


@pytest.fixture()
def project_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Project)


@pytest.fixture()
def organisation_content_type() -> ContentType:
    return ContentType.objects.get_for_model(Organisation)


@pytest.fixture
def manage_user_group_permission(db):  # type: ignore[no-untyped-def]
    return OrganisationPermissionModel.objects.get(key=MANAGE_USER_GROUPS)


@pytest.fixture()
def aws_credentials():  # type: ignore[no-untyped-def]
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture()
def dynamodb(aws_credentials):  # type: ignore[no-untyped-def]
    # TODO: move all wrapper tests to using moto
    with mock_dynamodb():
        yield boto3.resource("dynamodb")


@pytest.fixture()
def flagsmith_identities_table(
    dynamodb: DynamoDBServiceResource, settings: SettingsWrapper
) -> Table:
    table = dynamodb.create_table(
        TableName="flagsmith_identities",
        KeySchema=[
            {
                "AttributeName": "composite_key",
                "KeyType": "HASH",
            },
        ],
        AttributeDefinitions=[
            {"AttributeName": "composite_key", "AttributeType": "S"},
            {"AttributeName": "environment_api_key", "AttributeType": "S"},
            {"AttributeName": "identifier", "AttributeType": "S"},
            {"AttributeName": "identity_uuid", "AttributeType": "S"},
            {"AttributeName": "dashboard_alias", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "environment_api_key-identifier-index",
                "KeySchema": [
                    {"AttributeName": "environment_api_key", "KeyType": "HASH"},
                    {"AttributeName": "identifier", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "identity_uuid-index",
                "KeySchema": [{"AttributeName": "identity_uuid", "KeyType": "HASH"}],
                "Projection": {"ProjectionType": "ALL"},
            },
            {
                "IndexName": "environment_api_key-dashboard_alias-index-v2",
                "KeySchema": [
                    {"AttributeName": "environment_api_key", "KeyType": "HASH"},
                    {"AttributeName": "dashboard_alias", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "identifier",
                    ],
                },
            },
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    settings.IDENTITIES_TABLE_NAME_DYNAMO = table.name
    return table


@pytest.fixture()
def flagsmith_environments_v2_table(dynamodb: DynamoDBServiceResource) -> Table:
    return dynamodb.create_table(
        TableName="flagsmith_environments_v2",
        KeySchema=[
            {
                "AttributeName": "environment_id",
                "KeyType": "HASH",
            },
            {
                "AttributeName": "document_key",
                "KeyType": "RANGE",
            },
        ],
        AttributeDefinitions=[
            {"AttributeName": "environment_id", "AttributeType": "S"},
            {"AttributeName": "document_key", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )


@pytest.fixture()
def mock_github_client_generate_token(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "integrations.github.client.generate_token",
        return_value="mocked_token",
    )


@pytest.fixture()
def feature_external_resource(
    feature: Feature,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
    mock_github_client_generate_token: MagicMock,
) -> FeatureExternalResource:
    return FeatureExternalResource.objects.create(
        url="https://github.com/repositoryownertest/repositorynametest/issues/11",
        type="GITHUB_ISSUE",
        feature=feature,
        metadata='{"status": "open"}',
    )


@pytest.fixture()
def feature_external_resource_gh_pr(
    feature: Feature,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
    mock_github_client_generate_token: MagicMock,
) -> FeatureExternalResource:
    return FeatureExternalResource.objects.create(
        url="https://github.com/repositoryownertest/repositorynametest/pull/1",
        type="GITHUB_PR",
        feature=feature,
        metadata='{"status": "open"}',
    )


@pytest.fixture()
def feature_with_value_external_resource(
    feature_with_value: Feature,
    post_request_mock: MagicMock,
    mock_github_client_generate_token: MagicMock,
) -> FeatureExternalResource:
    return FeatureExternalResource.objects.create(
        url="https://github.com/repositoryownertest/repositorynametest/issues/11",
        type="GITHUB_ISSUE",
        feature=feature_with_value,
    )


@pytest.fixture()
def github_configuration(organisation: Organisation) -> GithubConfiguration:
    return GithubConfiguration.objects.create(  # type: ignore[no-any-return]
        organisation=organisation, installation_id=1234567
    )


@pytest.fixture()
def github_repository(
    github_configuration: GithubConfiguration,
    project: Project,
) -> GitHubRepository:
    return GitHubRepository.objects.create(  # type: ignore[no-any-return]
        github_configuration=github_configuration,
        repository_owner="repositoryownertest",
        repository_name="repositorynametest",
        project=project,
        tagging_enabled=True,
    )


@pytest.fixture(params=AdminClientAuthType.__args__)  # type: ignore[attr-defined]
def admin_client_auth_type(
    request: pytest.FixtureRequest,
) -> AdminClientAuthType:
    return request.param  # type: ignore[no-any-return]


@pytest.fixture
def admin_client_new(
    admin_client_auth_type: AdminClientAuthType,
    admin_client_original: APIClient,
    admin_master_api_key_client: APIClient,
) -> APIClient:
    if admin_client_auth_type == "master_api_key":
        return admin_master_api_key_client
    return admin_client_original


@pytest.fixture()
def superuser():  # type: ignore[no-untyped-def]
    return FFAdminUser.objects.create_superuser(  # type: ignore[no-untyped-call]
        email="superuser@example.com",
        password=FFAdminUser.objects.make_random_password(),
    )


@pytest.fixture()
def superuser_client(superuser: FFAdminUser, client: APIClient):  # type: ignore[no-untyped-def]
    client.force_login(superuser, backend="django.contrib.auth.backends.ModelBackend")
    return client


@pytest.fixture
def inspecting_handler() -> logging.Handler:
    """
    Fixture used to test the output of logger related output.
    """

    class InspectingHandler(logging.Handler):
        def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            super().__init__(*args, **kwargs)
            self.messages = []  # type: ignore[var-annotated]

        def handle(self, record: logging.LogRecord) -> None:  # type: ignore[override]
            self.messages.append(self.format(record))

    return InspectingHandler()


@pytest.fixture
def set_github_webhook_secret() -> None:
    from django.conf import settings

    settings.GITHUB_WEBHOOK_SECRET = "secret-key"
