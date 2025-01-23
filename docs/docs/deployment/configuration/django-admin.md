---
sidebar_label: Django Admin
title: Django Admin
sidebar_position: 100
---

# Django Admin

The Flagsmith API is a Django application. As such, certain administrative tasks can be performed with
[Django's built-in admin interface](https://docs.djangoproject.com/en/4.2/ref/contrib/admin/), which we refer to as
Django Admin.

:::danger

Improper use of Django Admin can cause data loss and make your Flagsmith instance unusable. Make sure to control who 
has access, and only perform tasks as directed by Flagsmith staff.

::: 

## Accessing Django Admin

Django Admin can be accessed from the `/admin/` route on the Flagsmith API. Note that the trailing slash is important.

Accessing Django Admin requires a user with
[`is_staff`](https://docs.djangoproject.com/en/4.2/ref/contrib/auth/#django.contrib.auth.models.User.is_staff) set.
This does not grant any additional permissions beyond accessing Django Admin itself.

A user with
[`is_superuser`](https://docs.djangoproject.com/en/4.2/ref/contrib/auth/#django.contrib.auth.models.User.is_superuser)
is granted all permissions. Note that superusers still require `is_staff` to access Django Admin.

You can obtain a user with these permissions using any of these methods:

* Use the [`createsuperuser` management command](/deployment/hosting/locally-api#locally) from a Flagsmith API shell.
* If no users exist yet,
  [visit the Initialise Config page](/deployment/hosting/locally-api#environments-with-no-direct-console-access-eg-heroku-ecs).
* Manually set the `is_staff` and `is_superuser` database fields for your user in the `users_ffadminuser` table.

## Authentication

You can log in to Django Admin using the same email and password you use to log in to Flagsmith, or using Google login.

### Email and password

To log in to Django Admin with a password, make sure the Flagsmith API has the `ENABLE_ADMIN_ACCESS_USER_PASS` 
environment variable set to `true`.

If your Flagsmith account does not have a password, you can create one using any of these methods:

* From the Flagsmith login page, click "Forgot password". Make sure your Flagsmith API is
  [configured to send emails](/deployment/hosting/locally-api#email).
* From a Flagsmith API shell, run `python manage.py changepassword your_email@example.com` and type a password.

### Google

Google accounts uses OAuth 2.0, which requires TLS.

To set up Google authentication for Django Admin, create an OAuth client ID and secret from
[Google Developer Console](https://console.developers.google.com/project). The redirect URI should point to
`/admin/admin_sso/assignment/end/` on your API domain.

Set your Google OAuth client ID and secret in the following Flagsmith API environment variables:

* `OAUTH_CLIENT_ID`
* `OAUTH_CLIENT_SECRET`

To log in with Google, click "Log in using SSO" from the Django Admin login page.
