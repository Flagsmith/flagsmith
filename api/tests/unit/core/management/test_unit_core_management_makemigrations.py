import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

DATABASES_LIST = list(settings.DATABASES.keys())


def test_makemigrations__without_name__raises_error() -> None:
    # Given / When
    # Then
    with pytest.raises(CommandError, match="--name/-n is a required argument"):
        call_command("makemigrations")


@pytest.mark.django_db(databases=DATABASES_LIST)
def test_makemigrations__with_check_changes__runs_without_error() -> None:
    # Given / When
    # Then
    call_command("makemigrations", check_changes=True)


@pytest.mark.django_db(databases=DATABASES_LIST)
def test_makemigrations__with_dry_run__runs_without_error() -> None:
    # Given / When
    # Then
    call_command("makemigrations", dry_run=True)


@pytest.mark.django_db(databases=DATABASES_LIST)
def test_makemigrations__with_name__runs_without_error() -> None:
    # Given / When
    # Then
    call_command("makemigrations", name="some_useful_name")
