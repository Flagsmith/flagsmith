from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import FFAdminUser, Invite


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = FFAdminUser
    list_display = ['email', 'get_number_of_organisations']

    fieldsets = UserAdmin.fieldsets + (
                    (_('Organisations'), {'fields': ('organisations',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'organisations',),
        }),
    )


admin.site.register(FFAdminUser, CustomUserAdmin)
admin.site.register(Invite)
