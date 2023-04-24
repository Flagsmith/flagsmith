---
sidebar_label: API
title: Flagsmith REST API
sidebar_position: 10
---

## Development Environment

Before running the application, you'll need to configure a database for the application. The steps to do this can be
found in the following section entitled 'Databases'.

```bash
virtualenv .venv
source .venv/bin/activate
pip install pip-tools
cd api
pip-sync requirements.txt requirements-dev.txt
python manage.py migrate
python manage.py runserver --nostatic
```

You can now visit `http://<your-server-domain:8000>/api/v1/users/config/init/` to create an initial Superuser and
provide DNS settings for your installation.

Note: if you're running on on MacOS and you find some issues installing the dependencies (specifically around pyre2),
you may need to run the following:

```bash
brew install cmake re2
```

The application can also be run locally using Docker Compose if required, however, it's beneficial to run locally using
the above steps as it gives you hot reloading. To run using docker compose, simply run the following command from the
project root:

```bash
git clone https://github.com/Flagsmith/self-hosted.git
cd self-hosted
docker-compose up
```

## Databases

Databases are configured in app/settings/\<env\>.py

The app is configured to use PostgreSQL for all environments.

When running locally, you'll need a local instance of postgres running. The easiest way to do this is to use docker
which is achievable with the following command:

`docker-compose -f docker/db.yaml up -d`

You'll also need to ensure that you have a value for POSTGRES_PASSWORD set as an environment variable on your
development machine.

When running on a Heroku-ish platform, the application reads the database connection in production from an environment
variable called `DATABASE_URL`. This should be configured in the Heroku-ish application configuration.

When running the application using Docker, it reads the database configuration from the settings located in
`app.settings.production`

## Initialising

The application is built using django which comes with a handy set of admin pages available at `/admin/`. To access
these, you'll need to create a super user. This user can also be used to access the admin pages or the application
itself if you have the frontend application running as well. This user can be created using the instructions below
dependent on your installation:

### Locally

```bash
cd api
python manage.py createsuperuser
```

### Environments with no direct console access (e.g. Heroku, ECS)

Once the app has been deployed, you can initialise your installation by accessing `/api/v1/users/config/init/`. This
will show a page with a basic form to set up some initial data for the platform. Each of the parameters in the form are
described below.

| Parameter name | Description                                                                                                                      |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Username       | A unique username to give the installation super user                                                                            |
| Email          | The email address to give the installation super user                                                                            |
| Password       | The password to give the installation super user                                                                                 |
| Site name      | A human readable name for the site, e.g. 'Flagsmith'                                                                             |
| Site domain    | The domain that the FE of the site will be running on, e.g. app.flagsmith.com. This will be used for e.g. password reset emails. |

Once you've created the super user, you can use the details to log in at `/admin/`. From here, you can create an
organisation and either create another user or simply assign the organisation to your admin user to begin using the
application.

Further information on the admin pages can be found [here](/deployment/configuration/django-admin).

## Deploying

### Using Heroku-ish Platform (e.g. Heroku, Dokku, Flynn)

The application should run on any Heroku-ish platform (e.g. Dokku, Flynn) by simply adding the required git repo and
pushing the code. The code for running the app is contained in the Procfile.

To get it running, you'll need to add the necessary config variables as outlined below.

### Using ElasticBeanstalk

The application will run within ElasticBeanstalk using the default Python setup. We've included the .ebextensions/ and
.elasticbeanstalk/ directories which will run on ElasticBeanstalk.

The changes required to run in your environment will be as follows

`.elasticbeanstalk/config.yml` - update application_name and default_region to the relevant variables for your setup.

`.ebextensions/options.config` - within the root of the project `generate.sh` will add in all environment variables that
are required using your chosen CI/CD. Alternatively, you can add your own `options.config`.

### Using Docker

If you want to run the entire Flagsmith platform, including the front end dashboard, take a look at our
[Flagsmith Docker repository](https://github.com/Flagsmith/self-hosted).

The application can be configured to run using docker with simply by running the following command:

```bash
git clone https://github.com/Flagsmith/self-hosted.git
cd self-hosted
docker-compose up
```

This will use some default settings created in the `docker-compose.yml` file located in the root of the project. These
should be changed before using in any production environments.

The docker container also accepts an argument that sets the access log file location for gunicorn. By default this is
set to /dev/null to maintain the default behaviour of gunicorn. It can either be set to `"-"` to redirect the logs to
stdout or to a location on the file system as required.

### Environment Variables

The application relies on the following environment variables to run:

#### Database Environment Variables

- `DATABASE_URL`: required by develop and production environments, should be a standard format database url e.g.
  postgres://user:password@host:port/db_name

You can also provide individual variables as below. Note that if a `DATABASE_URL` is defined, it will take precedent and
the below variables will be ignored.

- `DJANGO_DB_HOST`: Database hostname
- `DJANGO_DB_NAME`: Database name
- `DJANGO_DB_USER`: Database username
- `DJANGO_DB_PASSWORD`: Database password
- `DJANGO_DB_PORT`: Database port

#### Application Environment Variables

- `ENV`: string representing the current running environment, e.g. 'local', 'dev', 'prod'. Defaults to 'local'
- `DJANGO_SECRET_KEY`: secret key required by Django, if one isn't provided one will be created using
  `django.core.management.utilsget_random_secret_key`
- `LOG_LEVEL`: DJANGO logging level. Can be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `ACCESS_LOG_LOCATION`: The location to store web logs generated by gunicorn if running as a Docker container. If not
  set, no logs will be stored. If set to `-` the logs will be sent to `stdout`.
- `DJANGO_SETTINGS_MODULE`: python path to settings file for the given environment, e.g. "app.settings.develop"
- `ENABLE_GZIP_COMPRESSION`: If Django should gzip compress HTTP responses. Defaults to `False`.
- `GOOGLE_ANALYTICS_KEY`: if google analytics is required, add your tracking code
- `GOOGLE_SERVICE_ACCOUNT`: service account json for accessing the google API, used for getting usage of an
  organisation - needs access to analytics.readonly scope
- `INFLUXDB_TOKEN`: If you want to send API events to InfluxDB, specify this write token.
- `INFLUXDB_URL`: The URL for your InfluxDB database
- `INFLUXDB_ORG`: The organisation string for your InfluxDB API call.
- `GA_TABLE_ID`: GA table ID (view) to query when looking for organisation usage
- `USER_CREATE_PERMISSIONS`: set the permissions for creating new users, using a comma separated list of djoser or
  rest_framework permissions. Use this to turn off public user creation for self hosting. e.g.
  `'djoser.permissions.CurrentUserOrAdmin'` Defaults to `'rest_framework.permissions.AllowAny'`.
- `ALLOW_REGISTRATION_WITHOUT_INVITE`: Determines whether users can register without an invite. Defaults to True. Set to
  False or 0 to disable. Note that if disabled, new users must be invited via email.
- `ENABLE_EMAIL_ACTIVATION`: new user registration will go via email activation flow, default False
- `SENTRY_SDK_DSN`: If using Sentry, set the project DSN here.
- `SENTRY_TRACE_SAMPLE_RATE`: Float. If using Sentry, sets the trace sample rate. Defaults to 1.0.
- `DEFAULT_ORG_STORE_TRAITS_VALUE`: Boolean. Set this flag to ensure new organisations default to not persisting traits.
  Useful for data sensitive installations that don't want persistent traits.
- `OAUTH_CLIENT_ID`: Google OAuth Client ID to enable accessing django admin pages via Google OAuth. See the
  [Django Admin SSO package](https://pypi.org/project/django-admin-sso/) for information on how to set users up to
  access the admin pages via SSO.
- `OAUTH_CLIENT_SECRET`: Google OAuth Secret to enable accessing django admin pages via Google OAuth.
- `ENABLE_ADMIN_ACCESS_USER_PASS`: Boolean. Set this flag to enable login to admin panel using username and password.
- `USE_X_FORWARDED_HOST`: Boolean. Default `False`. Specifies whether to use the X-Forwarded-Host header in preference
  to the Host header. This should only be enabled if a proxy which sets this header is in use.
  [More Info](https://docs.djangoproject.com/en/4.0/ref/settings/#std:setting-USE_X_FORWARDED_HOST).
- `SECURE_PROXY_SSL_HEADER_NAME`: String. The name of the header looked for by Django's
  [`SECURE_PROXY_SSL_HEADER`](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-proxy-ssl-header). Defaults to
  `HTTP_X_FORWARDED_PROTO`.
- `SECURE_PROXY_SSL_HEADER_VALUE`: String. The value of the header looked for by Django's
  [`SECURE_PROXY_SSL_HEADER`](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-proxy-ssl-header). Defaults to
  `https`.
- `DJANGO_SECURE_REDIRECT_EXEMPT`: List. Passthrough of Django's
  [`SECURE_REDIRECT_EXEMPT`](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-redirect-exempt). Defaults to an
  empty list `[]`.
- `DJANGO_SECURE_REFERRER_POLICY`: String. Passthrough of Django's
  [`SECURE_REFERRER_POLICY`](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-referrer-policy). Defaults to
  `same-origin`.
- `DJANGO_SECURE_SSL_HOST`: String. Passthrough of Django's
  [`SECURE_SSL_HOST`](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-ssl-host). Defaults to `None`.
- `DJANGO_SECURE_SSL_REDIRECT`: Boolean. Passthrough of Django's
  [`SECURE_SSL_REDIRECT`](https://docs.djangoproject.com/en/4.0/ref/settings/#secure-ssl-redirect). Defaults to `False`.
- [`APPLICATION_INSIGHTS_CONNECTION_STRING`](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview).
  String. Connection string to set up Flagsmith to send telemetry to Azure Application Insights.
- [`OPENCENSUS_SAMPLING_RATE`](https://opencensus.io/tracing/sampling/probabilistic/): Float. The tracer sample rate.

#### Security Environment Variables

- `ALLOWED_ADMIN_IP_ADDRESSES`: restrict access to the django admin console to a comma separated list of IP addresses
  (e.g. `127.0.0.1,127.0.0.2`)
- `DJANGO_ALLOWED_HOSTS`: comma separated list of hosts the application will run on in the given environment
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma separated list of hosts to allow unsafe (POST, PUT) requests from. Useful for
  allowing localhost to set traits in development.
- `AXES_ONLY_USER_FAILURES`: If True, only lock based on username, and never lock based on IP if attempts exceed the
  limit. Otherwise utilize the existing IP and user locking logic. Defaults to `True`.
- `AXES_FAILURE_LIMIT`: The integer number of login attempts allowed before a record is created for the failed logins.
  Defaults to `10`.

#### Email Environment Variables

:::note

You can self host Flagsmith without setting up an email server/gateway. You can invite additional users to the platform
using invitation links, and the platform will run fine without email.

:::

:::tip

Flagsmith makes use of the `django_site` table to provide the domain name for email template links. You will need to
configure the record in this table to point to your domain for email links to work.

:::

- `SENDER_EMAIL`: Email address from which emails are sent
- `EMAIL_BACKEND`: One of:
  - `django.core.mail.backends.smtp.EmailBackend`
  - `sgbackend.SendGridBackend`
  - `django_ses.SESBackend`

If using `django.core.mail.backends.smtp.EmailBackend` you will need to configure:

- `EMAIL_HOST` = env("EMAIL_HOST", default='localhost')
- `EMAIL_HOST_USER` = env("EMAIL_HOST_USER", default=None)
- `EMAIL_HOST_PASSWORD` = env("EMAIL_HOST_PASSWORD", default=None)
- `EMAIL_PORT` = env("EMAIL_PORT", default=587)
- `EMAIL_USE_TLS` = env.bool("EMAIL_USE_TLS", default=True)

If using `sgbackend.SendGridBackend` you will need to configure:

- `SENDGRID_API_KEY`: API key for the Sendgrid account

If using AWS SES you will need to configure:

- `AWS_SES_REGION_NAME`: If using Amazon SES as the email provider, specify the region (e.g. eu-central-1) that contains
  your verified sender e-mail address. Defaults to us-east-1
- `AWS_SES_REGION_ENDPOINT`: ses region endpoint, e.g. email.eu-central-1.amazonaws.com. Required when using SES.
- `AWS_ACCESS_KEY_ID`: If using Amazon SES, these form part of your SES credentials.
- `AWS_SECRET_ACCESS_KEY`: If using Amazon SES, these form part of your SES credentials.

### API Telemetry

Flagsmith collects information about self hosted installations. This helps us understand how the platform is being used.
This data is _never_ shared outside of the organisation, and is anonymous by design. You can opt out of sending this
telemetry on startup by setting the `ENABLE_TELEMETRY` environment variable to `False`.

We collect the following data on startup per API server instance:

- Total number of Organisations
- Total number of Projects
- Total number of Environments
- Total number of Features
- Total number of Segments
- Total number of Users
- DEBUG django variable
- ENV django variable
- API server external IP address

### Creating a secret key

It is important to also set an environment variable on whatever platform you are using for `DJANGO_SECRET_KEY`. If one
is not set then Django will create one for you each time the application starts up, however, this will cause unexpected
behaviour as it is used by Django for encryption of e.g. session tokens, etc. To avoid these issues, please create set
the `DJANGO_SECRET_KEY` variable. Django recommends that this key should be at least 50 characters in length, however,
it is up to you to configure the key how you wish. Check the `get_random_secret_key()` method in the Django source code
if you want more information on what the key should look like.

## Running Tests

The application uses pytest for writing(appropritate use of fixtures) and running tests. Before running tests please
make sure that `DJANGO_SETTINGS_MODULE` env var is pointing to the right module, e.g. `app.settings.test`.

To run tests:

```bash
DJANGO_SETTINGS_MODULE=app.settings.test pytest
```

## Pre commit

The application uses pre-commit configuration ( `.pre-commit-config.yaml` ) to run `black`, `flake8` and `isort`
formatting before commits.

To install pre-commit:

```bash
# From the repository root
pip install pre-commit
pre-commit install
```

You can also manually run all the checks across the entire codebase with:

```bash
pre-commit run --all-files
```

## Adding dependencies

To add a python dependency, add it to requirements.txt / requirements-dev.txt with it's current version number.

## Caching

The application makes use of caching in a couple of locations:

1. Environment authentication - the application utilises an in memory cache for the environment object on all endpoints
   that use the X-Environment-Key header.
2. Environment flags - the application utilises an in memory cache for the flags returned when calling /flags. The
   number of seconds this is cached for is configurable using the environment variable `"CACHE_FLAGS_SECONDS"`
3. Project Segments - the application utilises an in memory cache for returning the segments for a given project. The
   number of seconds this is cached for is configurable using the environment variable
   `"CACHE_PROJECT_SEGMENTS_SECONDS"`.

## Unified Front End and Back End Build

You can run Flagsmith as a single application/docker container using our unified builds. These are available on
[Docker Hub](https://hub.docker.com/repository/docker/flagsmith/flagsmith) but you can also run the front end as part of
the Django Application. Steps to do this:

1. `cd frontend; npm run bundledjango`
2. `cd ../api; python manage.py collectstatic`
3. `python manage.py runserver`

### How it works

Webpack compiles a front end build, sourcing `api/app/templates/index.html`. It places the compiled JS and CSS assets to
`api/static` then copies the annotated `index.html` page to `api/app/templates/webpack/index.html`.

The Django `collectstatic` command then copies all the additional static assets that Django needs, including
`api/app/templates/webpack/index.html`, into `api/static`.

## Information for Developers working on the project

### Stack

- Python
- Django
- Django Rest Framework

### Development Environment for Contributers

We're using [pip-tools](https://github.com/jazzband/pip-tools) to manage packages and dependencies.

To upgrade packages or add new ones:

```bash
pip install -r requirements-dev.txt
pip-compile
```

### Requirements with pip-tools

We are using [pip-tools](https://github.com/jazzband/pip-tools) to manage dependencies.

To add a new library to the project, edit requirements.in, then:

```bash
# This step will overwrite requirements.txt
pip-compile requirements.in
pip install -r requirements.txt
```
