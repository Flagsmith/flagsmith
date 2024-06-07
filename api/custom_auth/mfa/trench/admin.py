from django.contrib import admin

from custom_auth.mfa.trench.models import MFAMethod


@admin.register(MFAMethod)
class MFAMethodAdmin(admin.ModelAdmin):
    pass
