from django.contrib import admin

# Override admin template to remove form with `email` and `password`.
admin.site.login_template = "login.html"
