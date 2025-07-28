---
title: "Initial Setup"
description: "How to initialize the instance and create the first superuser."
sidebar_position: 10
---

The application is built using django which comes with a handy set of admin pages available at `/admin/`. To access these, you'll need to create a super user. This user can also be used to access the admin pages or the application itself if you have the frontend application running as well. This user can be created using the instructions below dependent on your installation:

### Locally

```bash
cd api
python manage.py createsuperuser
```

### Environments with no direct console access (e.g. Heroku, ECS)

Once the app has been deployed, you can initialise your installation by accessing `/api/v1/users/config/init/`. This will show a page with a basic form to set up some initial data for the platform. Each of the parameters in the form are described below.

| Parameter name  | Description                                                                                                                      |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Username        | A unique username to give the installation super user                                                                            |
| Email           | The email address to give the installation super user                                                                            |
| Password        | The password to give the installation super user                                                                                 |
| Site name       | A human readable name for the site, e.g. 'Flagsmith'                                                                             |
| Site domain[^1] | The domain that the FE of the site will be running on, e.g. app.flagsmith.com. This will be used for e.g. password reset emails. |

[^1]: It is important that this is correct as it is used in the password reset emails to construct the reset link. 