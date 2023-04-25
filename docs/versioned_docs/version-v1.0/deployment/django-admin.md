---
sidebar_label: Django Admin
title: Django Admin
sidebar_position: 100
---

# Django Admin

Since the application is built using Django, it benefits from the django admin pages. Flagsmith is built to utilise the
Django admin site for certain aspects of the platform. If you are self hosting, you may find it useful to access these
pages at certain times.

## Authentication

The admin pages are only available to uses that are designated as 'super users'. This can only be done when first
setting up the platform or via the database. If you're just starting out, you can follow the instructions
[here](/deployment/hosting/locally-api#Initialising), otherwise, you need to set the `is_staff` and `is_superuser` flags
against any of the users in your database.

Once you have a user, you can access the django admin pages at `/admin`. You will be prompted to log in with the
credentials of any of your super users.

## Admin Pages

### Organisation

The key pages that one might want to access are the ones that configuration organisations on the platform. From the home
page of the admin, you'll see an link to `Organisations` about halfway down the page. From here, you can manage the
organisations on your platform as required. For example, SAML configuration data must be set via these pages.
