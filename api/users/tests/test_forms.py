from users.forms import CustomUserAdminForm


def test_custom_user_admin_form_empty_value_of_username_is_none(db):
    # Given
    form = CustomUserAdminForm({"email": "test@mail.com"})
    # When
    form.is_valid()
    # Then
    assert form.cleaned_data["username"] is None
