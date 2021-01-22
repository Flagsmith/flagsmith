from django.conf import settings
from django.contrib.admin import AdminSite


class CustomAdminSite(AdminSite):
    def each_context(self, request):
        context = super(CustomAdminSite, self).each_context(request)
        # send context to the templates to confirm whether to show the regular username
        # and password login form. If not True, only SSO login will be available.
        context["show_login_form"] = settings.ENABLE_ADMIN_ACCESS_USER_PASS
        return context
