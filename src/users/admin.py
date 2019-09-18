from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import FFAdminUser, Invite


@admin.register(FFAdminUser)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = FFAdminUser

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2',),
        }),
    )

    date_hierarchy = 'date_joined'

    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
        'date_joined',
    )

    list_filter = ('is_staff', 'is_active', 'date_joined', 'organisations', )

    search_fields = ('email', 'username', 'first_name', 'last_name', )


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    date_hierarchy = 'date_created'
    list_display = ('email', 'invited_by', 'organisation', 'date_created', )
    list_filter = ('date_created', 'organisation', )
    list_select_related = ('organisation', 'invited_by', )
    raw_id_fields = ('invited_by', )
    search_fields = (
        'email',
        'invited_by__email',
        'invited_by__username',
        'invited_by__first_name',
        'invited_by__last_name',
        'organisation__name',
    )
