import pytest


@pytest.fixture()
def superuser(django_user_model):  # type: ignore[no-untyped-def]
    return django_user_model.objects.create_superuser(
        email="superuser@example.com",
        password=django_user_model.objects.make_random_password(),
    )


@pytest.fixture()
def superuser_authenticated_client(superuser, client):  # type: ignore[no-untyped-def]
    client.force_login(superuser, backend="django.contrib.auth.backends.ModelBackend")
    return client
