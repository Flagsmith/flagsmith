import json
from unittest.case import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment, STRING, INTEGER
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from util.tests import Helper


class SDKTraitsTest(APITestCase):
    JSON = "application/json"

    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test organisation")
        project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        self.environment = Environment.objects.create(
            name="Test environment", project=project
        )
        self.identity = Identity.objects.create(
            identifier="test-user", environment=self.environment
        )
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        self.trait_key = "trait_key"
        self.trait_value = "trait_value"

    def test_can_set_trait_for_an_identity(self):
        # Given
        url = reverse("api-v1:sdk-traits-list")

        # When
        res = self.client.post(
            url, data=self._generate_json_trait_data(), content_type=self.JSON
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Trait.objects.filter(
            identity=self.identity, trait_key=self.trait_key
        ).exists()

    def test_cannot_set_trait_for_an_identity_for_organisations_without_persistence(
        self,
    ):
        # Given
        url = reverse("api-v1:sdk-traits-list")

        # an organisation that is configured to not store traits
        self.organisation.persist_trait_data = False
        self.organisation.save()

        # When
        response = self.client.post(
            url, data=self._generate_json_trait_data(), content_type=self.JSON
        )

        # Then
        # the request fails
        assert response.status_code == status.HTTP_403_FORBIDDEN
        response_json = response.json()
        assert response_json["detail"] == (
            "Organisation is not authorised to store traits."
        )

        # and no traits are stored
        assert Trait.objects.count() == 0

    def test_can_set_trait_with_boolean_value_for_an_identity(self):
        # Given
        url = reverse("api-v1:sdk-traits-list")
        trait_value = True

        # When
        res = self.client.post(
            url,
            data=self._generate_json_trait_data(trait_value=trait_value),
            content_type=self.JSON,
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert (
            Trait.objects.get(
                identity=self.identity, trait_key=self.trait_key
            ).get_trait_value()
            == trait_value
        )

    def test_can_set_trait_with_identity_value_for_an_identity(self):
        # Given
        url = reverse("api-v1:sdk-traits-list")
        trait_value = 12

        # When
        res = self.client.post(
            url,
            data=self._generate_json_trait_data(trait_value=trait_value),
            content_type=self.JSON,
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert (
            Trait.objects.get(
                identity=self.identity, trait_key=self.trait_key
            ).get_trait_value()
            == trait_value
        )

    def test_can_set_trait_with_float_value_for_an_identity(self):
        # Given
        url = reverse("api-v1:sdk-traits-list")
        float_trait_value = 10.5

        # When
        res = self.client.post(
            url,
            data=self._generate_json_trait_data(trait_value=float_trait_value),
            content_type=self.JSON,
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert (
                Trait.objects.get(
                    identity=self.identity, trait_key=self.trait_key
                ).get_trait_value() == float_trait_value
        )

    def test_add_trait_creates_identity_if_it_doesnt_exist(self):
        # Given
        url = reverse("api-v1:sdk-traits-list")
        identifier = "new-identity"

        # When
        res = self.client.post(
            url,
            data=self._generate_json_trait_data(identifier=identifier),
            content_type=self.JSON,
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Identity.objects.filter(
            identifier=identifier, environment=self.environment
        ).exists()

        # and
        assert Trait.objects.filter(
            identity__identifier=identifier, trait_key=self.trait_key
        ).exists()

    def test_trait_is_updated_if_already_exists(self):
        # Given
        url = reverse("api-v1:sdk-traits-list")
        trait = Trait.objects.create(
            trait_key=self.trait_key,
            value_type=STRING,
            string_value=self.trait_value,
            identity=self.identity,
        )
        new_value = "Some new value"

        # When
        self.client.post(
            url,
            data=self._generate_json_trait_data(trait_value=new_value),
            content_type=self.JSON,
        )

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == new_value

    def test_increment_value_increments_trait_value_if_value_positive_integer(self):
        # Given
        initial_value = 2
        increment_by = 2

        url = reverse("api-v1:sdk-traits-increment-value")
        trait = Trait.objects.create(
            identity=self.identity,
            trait_key=self.trait_key,
            value_type=INTEGER,
            integer_value=initial_value,
        )
        data = {
            "trait_key": self.trait_key,
            "identifier": self.identity.identifier,
            "increment_by": increment_by,
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == initial_value + increment_by

    def test_increment_value_decrements_trait_value_if_value_negative_integer(self):
        # Given
        initial_value = 2
        increment_by = -2

        url = reverse("api-v1:sdk-traits-increment-value")
        trait = Trait.objects.create(
            identity=self.identity,
            trait_key=self.trait_key,
            value_type=INTEGER,
            integer_value=initial_value,
        )
        data = {
            "trait_key": self.trait_key,
            "identifier": self.identity.identifier,
            "increment_by": increment_by,
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == initial_value + increment_by

    def test_increment_value_initialises_trait_with_a_value_of_zero_if_it_doesnt_exist(
        self,
    ):
        # Given
        increment_by = 1

        url = reverse("api-v1:sdk-traits-increment-value")
        data = {
            "trait_key": self.trait_key,
            "identifier": self.identity.identifier,
            "increment_by": increment_by,
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait = Trait.objects.get(trait_key=self.trait_key, identity=self.identity)
        assert trait.get_trait_value() == increment_by

    def test_increment_value_returns_400_if_trait_value_not_integer(self):
        # Given
        url = reverse("api-v1:sdk-traits-increment-value")
        Trait.objects.create(
            identity=self.identity,
            trait_key=self.trait_key,
            value_type=STRING,
            string_value="str",
        )
        data = {
            "trait_key": self.trait_key,
            "identifier": self.identity.identifier,
            "increment_by": 2,
        }

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_bulk_create_traits(self):
        # Given
        num_traits = 20
        url = reverse("api-v1:sdk-traits-bulk-create")
        traits = [
            self._generate_trait_data(trait_key=f"trait_{i}") for i in range(num_traits)
        ]

        # When
        response = self.client.put(
            url, data=json.dumps(traits), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Trait.objects.filter(identity=self.identity).count() == num_traits

    def test_sending_null_value_in_bulk_create_deletes_trait_for_identity(self):
        # Given
        url = reverse("api-v1:sdk-traits-bulk-create")
        trait_to_delete = Trait.objects.create(
            trait_key=self.trait_key,
            value_type=STRING,
            string_value=self.trait_value,
            identity=self.identity,
        )
        trait_key_to_keep = "another_trait_key"
        trait_to_keep = Trait.objects.create(
            trait_key=trait_key_to_keep,
            value_type=STRING,
            string_value="value is irrelevant",
            identity=self.identity,
        )
        data = [
            {
                "identity": {"identifier": self.identity.identifier},
                "trait_key": self.trait_key,
                "trait_value": None,
            }
        ]

        # When
        response = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        # the request is successful
        assert response.status_code == status.HTTP_200_OK

        # and the trait is deleted
        assert not Trait.objects.filter(id=trait_to_delete.id).exists()

        # but the trait missing from the request is left untouched
        assert Trait.objects.filter(id=trait_to_keep.id).exists()

    def test_bulk_create_traits_when_float_value_sent_then_trait_value_scorrect(self):
        # Given
        num_traits = 5
        url = reverse("api-v1:sdk-traits-bulk-create")
        traits = [
            self._generate_trait_data(trait_key=f"trait_{i}") for i in range(num_traits)
        ]

        # add some bad data to test
        float_trait_key = "float_key_999"
        float_trait_value = 45.88
        traits.append(
            {
                "trait_value": float_trait_value,
                "trait_key": float_trait_key,
                "identity": {"identifier": self.identity.identifier}
            }
        )

        # When
        response = self.client.put(
            url, data=json.dumps(traits), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert Trait.objects.filter(identity=self.identity).count() == num_traits + 1

        # and
        assert (
                Trait.objects.get(
                    identity=self.identity, trait_key=float_trait_key
                ).get_trait_value() == float_trait_value
        )

    def _generate_trait_data(self, identifier=None, trait_key=None, trait_value=None):
        identifier = identifier or self.identity.identifier
        trait_key = trait_key or self.trait_key
        trait_value = trait_value or self.trait_value

        return {
            "identity": {"identifier": identifier},
            "trait_key": trait_key,
            "trait_value": trait_value,
        }

    def _generate_json_trait_data(
        self, identifier=None, trait_key=None, trait_value=None
    ):
        return json.dumps(self._generate_trait_data(identifier, trait_key, trait_value))


@pytest.mark.django_db
class TraitViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name="Test org")
        user.add_organisation(organisation, OrganisationRole.ADMIN)

        self.project = Project.objects.create(
            name="Test project", organisation=organisation
        )
        self.environment = Environment.objects.create(
            name="Test environment", project=self.project
        )
        self.identity = Identity.objects.create(
            identifier="test-user", environment=self.environment
        )

    def test_can_delete_trait(self):
        # Given
        trait_key = "trait_key"
        trait_value = "trait_value"
        trait = Trait.objects.create(
            identity=self.identity,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )
        url = reverse(
            "api-v1:environments:identities-traits-detail",
            args=[self.environment.api_key, self.identity.id, trait.id],
        )

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert not Trait.objects.filter(pk=trait.id).exists()

    def test_delete_trait_only_deletes_single_trait_if_query_param_not_provided(self):
        # Given
        trait_key = "trait_key"
        trait_value = "trait_value"
        identity_2 = Identity.objects.create(
            identifier="test-user-2", environment=self.environment
        )

        trait = Trait.objects.create(
            identity=self.identity,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )
        trait_2 = Trait.objects.create(
            identity=identity_2,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )

        url = reverse(
            "api-v1:environments:identities-traits-detail",
            args=[self.environment.api_key, self.identity.id, trait.id],
        )

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert Trait.objects.filter(pk=trait_2.id).exists()

    def test_delete_trait_deletes_all_traits_if_query_param_provided(self):
        # Given
        trait_key = "trait_key"
        trait_value = "trait_value"
        identity_2 = Identity.objects.create(
            identifier="test-user-2", environment=self.environment
        )

        trait = Trait.objects.create(
            identity=self.identity,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )
        trait_2 = Trait.objects.create(
            identity=identity_2,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )

        base_url = reverse(
            "api-v1:environments:identities-traits-detail",
            args=[self.environment.api_key, self.identity.id, trait.id],
        )
        url = base_url + "?deleteAllMatchingTraits=true"

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert not Trait.objects.filter(pk=trait_2.id).exists()

    def test_delete_trait_only_deletes_traits_in_current_environment(self):
        # Given
        environment_2 = Environment.objects.create(
            name="Test environment", project=self.project
        )
        trait_key = "trait_key"
        trait_value = "trait_value"
        identity_2 = Identity.objects.create(
            identifier="test-user-2", environment=environment_2
        )

        trait = Trait.objects.create(
            identity=self.identity,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )
        trait_2 = Trait.objects.create(
            identity=identity_2,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )

        base_url = reverse(
            "api-v1:environments:identities-traits-detail",
            args=[self.environment.api_key, self.identity.id, trait.id],
        )
        url = base_url + "?deleteAllMatchingTraits=true"

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert Trait.objects.filter(pk=trait_2.id).exists()
