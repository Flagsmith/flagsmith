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
    list_display = ['email', 'get_number_of_organisations']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'organisations',),
        })
    )

    fieldsets = UserAdmin.fieldsets + (
        (_('Organisations'), {'fields': ('organisations',)}),
        (_('Statistics'), {'fields': ('get_number_of_organisations',
                                      'get_number_of_projects',
                                      'get_number_of_features',
                                      'get_number_of_environments')})

    )
    add_form = CustomUserCreationForm
    date_hierarchy = 'date_joined'
    fieldsets = UserAdmin.fieldsets + (
        (_('Organisations'), {'fields': ('organisations', )}),
    )
    form = CustomUserChangeForm
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
    model = FFAdminUser
    search_fields = ('email', 'username', 'first_name', 'last_name', )

    readonly_fields = ['get_number_of_organisations',
                       'get_number_of_projects',
                       'get_number_of_features',
                       'get_number_of_environments']

    def get_number_of_organisations(self, obj):
        return obj.get_number_of_organisations()
    get_number_of_organisations.short_description = "Number of Organisations"

    def get_number_of_projects(self, obj):
        return obj.get_number_of_projects()
    get_number_of_projects.short_description = "Number of Projects"

    def get_number_of_features(self, obj):
        return obj.get_number_of_features()
    get_number_of_features.short_description = "Number of Features"

    def get_number_of_environments(self, obj):
        return obj.get_number_of_environments()
    get_number_of_environments.short_description = "Number of Environments"


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
