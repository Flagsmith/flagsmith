from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class CustomAdminConfig(AdminConfig):
    default_site = "core.custom_admin.admin.CustomAdminSite"


class CustomAdminAppConfig(AppConfig):
    name = "core.custom_admin"
