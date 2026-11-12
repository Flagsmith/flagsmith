from django.contrib import admin
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy


class CustomTokenAdmin(TokenAdmin):
    search_fields = ("user__email",)


admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, CustomTokenAdmin)
