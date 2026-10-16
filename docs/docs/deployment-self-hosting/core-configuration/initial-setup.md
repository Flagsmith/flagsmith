---
title: "Initial Setup"
description: "How to initialise the instance and create the first superuser."
sidebar_position: 10
---

A new Flagsmith instance has no users. The first account you create is a superuser: it can manage the instance and sign
in to the Django Admin at `/admin/`. Pick one of the options below, depending on your installation.

## From the dashboard (recommended)

Open the dashboard, e.g. [http://localhost:8000](http://localhost:8000) if you are running our
[Docker Compose file](/deployment-self-hosting/hosting-guides/docker). While the instance has no users, the dashboard
shows a **Welcome to Flagsmith** screen instead of the login page. Select **Get Started**, enter your name, email and
password, then name your first organisation.

Nothing is printed to the logs for this step. Once the first account exists, the dashboard shows the usual login and
sign-up pages.

## From the command line

From a running Flagsmith container:

```bash
flagsmith createsuperuser
```

For a local installation from source:

```bash
cd api
python manage.py createsuperuser
```

## Automatically on startup

Set `ALLOW_ADMIN_INITIATION_VIA_CLI` to `true` to let the `bootstrap` command create a superuser (`ADMIN_EMAIL`), an
organisation (`ORGANISATION_NAME`) and a project (`PROJECT_NAME`). Each step is skipped if a user, organisation or
project already exists.

`bootstrap` runs automatically only when the container starts with `migrate-and-serve`. If you run `migrate` and `serve`
as separate containers, as our Docker Compose file does, run `flagsmith bootstrap` yourself once migrations have
finished. It prints a link to set the superuser's password:

```txt
Superuser "admin@example.com" created successfully.
Please go to the following page and choose a password: http://localhost:8000/password-reset/confirm/.../...
```

## Without the dashboard

If you only run the API, you can initialise your installation by visiting `/api/v1/users/config/init/`. This page shows
a basic form; submitting it creates the superuser and returns a link to set its password.

| Parameter name  | Description                                                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Email           | The email address to give the installation superuser                                                                                   |
| Site name       | A human-readable name for the site, e.g. 'Flagsmith'                                                                                   |
| Site domain[^1] | The domain that the frontend of the site will be running on, e.g. app.flagsmith.com. This will be used for e.g. password reset emails. |

[^1]: It is important that this is correct as it is used in the password reset emails to construct the reset link.
