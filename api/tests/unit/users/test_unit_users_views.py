import json

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
from users.models import FFAdminUser


@pytest.mark.django_db
def test_delete_user():
    def delete_user(
        user: FFAdminUser, password: str, delete_orphan_organisations: bool = True
    ):
        client = APIClient()
        client.force_authenticate(user)
        data = {
            "current_password": password,
            "delete_orphan_organisations": delete_orphan_organisations,
        }
        url = "/api/v1/auth/users/me/"
        return client.delete(
            url, data=json.dumps(data), content_type="application/json"
        )

    # create a couple of users
    email1 = "test1@example.com"
    email2 = "test2@example.com"
    email3 = "test3@example.com"
    password = "password"
    user1 = FFAdminUser.objects.create(email=email1)
    user1.set_password(password)
    user2 = FFAdminUser.objects.create(email=email2)
    user2.set_password(password)
    user3 = FFAdminUser.objects.create(email=email3)
    user3.set_password(password)

    # crete some organizations
    org1 = Organisation.objects.create(name="org1")
    org2 = Organisation.objects.create(name="org2")
    org3 = Organisation.objects.create(name="org3")

    # add the test user 1 to all the organizations
    org1.users.add(user1)
    org2.users.add(user1)
    org3.users.add(user1)

    # add test user 2 to org2 and user 3 to to org1
    org2.users.add(user2)
    org1.users.add(user3)

    # Configuration: org1: [user1, user3], org2: [user1, user2], org3: [user1]

    # Delete user2
    response = delete_user(user2, password)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email2).exists()

    # All organisations remain since user 2 has org2 as only organization and it has 2 users
    assert Organisation.objects.filter(name="org3").count() == 1
    assert Organisation.objects.filter(name="org1").count() == 1
    assert Organisation.objects.filter(name="org2").count() == 1

    # Delete user1
    response = delete_user(user1, password)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email1).exists()

    # organization org3 and org2 are deleted since its only user is user1
    assert Organisation.objects.filter(name="org3").count() == 0
    assert Organisation.objects.filter(name="org2").count() == 0

    # org1 remain
    assert Organisation.objects.filter(name="org1").count() == 1

    # user3 remain
    assert FFAdminUser.objects.filter(email=email3).exists()

    # Delete user3
    response = delete_user(user3, password, False)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email3).exists()
    assert Organisation.objects.filter(name="org1").count() == 1
