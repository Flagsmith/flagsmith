from typing import Generator

import pytest
from django.contrib.postgres.fields import ArrayField
from django.db import connection, models
from django.db.models import F, Value
from django.test.utils import isolate_apps

from projects.code_references.db_helpers import ArrayContains


@pytest.fixture()
def names_model(db: None) -> Generator[type[models.Model]]:
    with isolate_apps("projects.code_references"):

        class NamesModel(models.Model):
            names = ArrayField(models.TextField(), default=list)

            class Meta:
                app_label = "projects.code_references"

        with connection.schema_editor() as editor:
            editor.create_model(NamesModel)

        yield NamesModel


def test_ArrayContains__matches_when_value_present_in_array(
    names_model: models.Model,
) -> None:
    # Given
    names_model.objects.create(names=["john", "esme"])  # type: ignore[attr-defined]

    # When
    result = names_model.objects.annotate(  # type: ignore[attr-defined]
        has_name=ArrayContains(F("names"), Value("esme")),
    ).get()

    # Then
    assert result.has_name is True


def test_ArrayContains__does_not_match_when_value_absent_from_array(
    names_model: models.Model,
) -> None:
    # Given
    names_model.objects.create(names=["john"])  # type: ignore[attr-defined]

    # When
    result = names_model.objects.annotate(  # type: ignore[attr-defined]
        has_name=ArrayContains(F("names"), Value("lisa")),
    ).get()

    # Then
    assert result.has_name is False


def test_ArrayContains__filters_queryset_correctly(
    names_model: models.Model,
) -> None:
    # Given
    matching = names_model.objects.create(names=["john", "esme"])  # type: ignore[attr-defined]
    names_model.objects.create(names=["lisa"])  # type: ignore[attr-defined]

    # When
    results = names_model.objects.annotate(  # type: ignore[attr-defined]
        has_name=ArrayContains(F("names"), Value("john")),
    ).filter(has_name=True)

    # Then
    assert list(results) == [matching]


def test_ArrayContains__does_not_match_empty_array(
    names_model: models.Model,
) -> None:
    # Given
    names_model.objects.create(names=[])  # type: ignore[attr-defined]

    # When
    result = names_model.objects.annotate(  # type: ignore[attr-defined]
        has_name=ArrayContains(F("names"), Value("kiefer")),
    ).get()

    # Then
    assert result.has_name is False
