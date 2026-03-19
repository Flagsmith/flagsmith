import pytest

from users.signals import warn_insecure


@pytest.mark.django_db
def test_warn_insecure__no_users_exist__emits_runtime_warning(
    recwarn, django_user_model
):  # type: ignore[no-untyped-def]
    # Given / When
    warn_insecure(django_user_model)  # type: ignore[no-untyped-call]

    # Then
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert issubclass(w.category, RuntimeWarning)


@pytest.mark.django_db
def test_warn_insecure__user_exists__emits_no_warning(  # type: ignore[no-untyped-def]
    admin_user, recwarn, django_user_model
):
    # Given / When
    warn_insecure(django_user_model)  # type: ignore[no-untyped-call]

    # Then
    assert len(recwarn) == 0
