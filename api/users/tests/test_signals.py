import pytest

from users.signals import warn_insecure


@pytest.mark.django_db
def test_warn_insecure_emits_a_warning_when_no_user_exists(recwarn):
    # When
    warn_insecure(None)

    # Then
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert issubclass(w.category, RuntimeWarning)


@pytest.mark.django_db
def test_warn_insecure_emits_no_warning_when_user_exists(admin_user, recwarn):
    # When
    warn_insecure(None)

    # Then
    assert len(recwarn) == 0
