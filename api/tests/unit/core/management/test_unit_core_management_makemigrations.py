import pytest
from django.conf import settings
from django.core.management import CommandError, call_command

DATABASES_LIST = list(settings.DATABASES.keys())


def test_makemigrations_without_name_raises_error() -> None:
    with pytest.raises(CommandError, match="--name/-n is a required argument"):
        call_command("makemigrations")


@pytest.mark.django_db(databases=DATABASES_LIST)
def test_makemigrations_with_check_changes_runs_without_error() -> None:
    call_command("makemigrations", check_changes=True)


@pytest.mark.django_db(databases=DATABASES_LIST)
def test_makemigrations_with_dry_run_runs_without_error() -> None:
    call_command("makemigrations", dry_run=True)


@pytest.mark.django_db(databases=DATABASES_LIST)
def test_makemigrations_with_name_runs_without_error() -> None:
    call_command("makemigrations", name="some_useful_name")
