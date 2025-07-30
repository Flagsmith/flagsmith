import pytest

from users.signals import warn_insecure


@pytest.mark.django_db
def test_warn_insecure_emits_a_warning_when_no_user_exists(recwarn, django_user_model):  # type: ignore[no-untyped-def]  # noqa: E501
    # When
    warn_insecure(django_user_model)  # type: ignore[no-untyped-call]

    # Then
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert issubclass(w.category, RuntimeWarning)


@pytest.mark.django_db
def test_warn_insecure_emits_no_warning_when_user_exists(  # type: ignore[no-untyped-def]
    admin_user, recwarn, django_user_model
):
    # When
    warn_insecure(django_user_model)  # type: ignore[no-untyped-call]

    # Then
    assert len(recwarn) == 0
