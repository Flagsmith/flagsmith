import pytest


@pytest.fixture()
def superuser(django_user_model):
    return django_user_model.objects.create_superuser(
        email="superuser@example.com",
        password=django_user_model.objects.make_random_password(),
    )


@pytest.fixture()
def superuser_authenticated_client(superuser, client):
    client.force_login(superuser, backend="django.contrib.auth.backends.ModelBackend")
    return client
