---
sidebar_label: API
title: Flagsmith REST API
sidebar_position: 10
---

## Setting Up

Before running the application, you'll need to configure a database for the application. The steps to do this can be
found in the following section entitled 'Databases'.

```bash
cd api
make install
make django-migrate
make serve
```

You can now visit `http://<your-server-domain:8000>/api/v1/users/config/init/` to create an initial Superuser and
provide DNS settings for your installation or run `make test` from the `api` directory to run the test suite.

Note: if you're running on on MacOS and you find some issues installing the dependencies (specifically around pyre2),
you may need to run the following:

```bash
brew install cmake re2
```

The application can also be run locally using Docker Compose if required, however, it's beneficial to run locally using
the above steps as it gives you hot reloading. To run using docker compose, run the following command from the project
root:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
docker-compose -f docker-compose.yml up
```

## Databases

Databases are configured in app/settings/\<env\>.py

The app is configured to use PostgreSQL for all environments.

When running locally, you'll need a local instance of postgres running. The easiest way to do this is to use docker
which is achievable with the following command:

`docker-compose -f docker/db.yml up -d`

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

| Parameter name  | Description                                                                                                                      |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Username        | A unique username to give the installation super user                                                                            |
| Email           | The email address to give the installation super user                                                                            |
| Password        | The password to give the installation super user                                                                                 |
| Site name       | A human readable name for the site, e.g. 'Flagsmith'                                                                             |
| Site domain[^1] | The domain that the FE of the site will be running on, e.g. app.flagsmith.com. This will be used for e.g. password reset emails. |

Once you've created the super user, you can use the details to log in at `/admin/`. From here, you can create an
organisation and either create another user or assign the organisation to your admin user to begin using the
application.

Further information on the admin pages can be found [here](/deployment/configuration/django-admin).

[^1]:

Your Flagsmith's domain can also be configured via the `FLAGSMITH_DOMAIN` environment variable. See the
[full list](#application-environment-variables) of variables used for configuration.

## Deploying

### Using Docker

If you want to run the entire Flagsmith platform, including the front end dashboard:

```bash
curl -o docker-compose.yml https://raw.githubusercontent.com/Flagsmith/flagsmith/main/docker-compose.yml
docker-compose -f docker-compose.yml up
```

This will use some default settings created in the `docker-compose.yml` file located in the root of the project. These
should be changed before using in any production environments.

The docker container also accepts an argument that sets the access log file location for gunicorn. By default this is
set to /dev/null to maintain the default behaviour of gunicorn. It can either be set to `"-"` to redirect the logs to
stdout or to a location on the file system as required.

### Environment Variables

The application relies on the following environment variables to run:

#### Database Environment Variables

- `DATABASE_URL`: (required) configure the database to connect to. Should be a standard format database url e.g.
  postgres://user:password@host:port/db_name
- `REPLICA_DATABASE_URLS`: (optional) configure an optional number of read replicas. Should be a comma separated list of
  standard format database urls. e.g.
  postgres://user:password@replica1.db.host/flagsmith,postgres://user:password@replica2.db.host/flagsmith
- `REPLICA_DATABASE_URLS_DELIMITER`: (optional) set the delimiter to use for separating replica database urls when using
  `REPLICA_DATABASE_URLS` variable. Defaults to `,`. This is useful if, for example, the comma character appears in one
  or more passwords.

You can also provide individual variables as below. Note that if a `DATABASE_URL` is defined, it will take precedent and
the below variables will be ignored.

- `DJANGO_DB_HOST`: Database hostname
- `DJANGO_DB_NAME`: Database name
- `DJANGO_DB_USER`: Database username
- `DJANGO_DB_PASSWORD`: Database password
- `DJANGO_DB_PORT`: Database port

#### GitHub Auth Environment Variables

- `GITHUB_CLIENT_ID`: Used for GitHub OAuth configuration, provided in your **OAuth Apps** settings.
- `GITHUB_CLIENT_SECRET`: Used for GitHub OAuth configuration, provided in your **OAuth Apps** settings.

#### Application Environment Variables

- `ENVIRONMENT`: string representing the current running environment, such as "local", "dev", "staging" or "production".
  Defaults to 'local'
- `DJANGO_SECRET_KEY`: secret key required by Django, if one isn't provided one will be created using
  `django.core.management.utils.get_random_secret_key`. WARNING: If running multiple API instances, its vital that you
  define a shared DJANGO_SECRET_KEY.
- `LOG_LEVEL`: DJANGO logging level. Can be one of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- `LOG_FORMAT`: Can be `generic` (plain-text) or `json`. Defaults to `generic`.
- `GUNICORN_CMD_ARGS`: Gunicorn command line arguments. Overrides Flagsmith's defaults. See
  [Gunicorn documentation](https://docs.gunicorn.org/en/stable/settings.html) for reference.
- `ACCESS_LOG_FORMAT`: Message format for Gunicorn's access log. See
  [variable details](https://docs.gunicorn.org/en/stable/settings.html#access-log-format) to define your own format.
- `ACCESS_LOG_LOCATION`: The location to store web logs generated by Gunicorn if running as a Docker container. If not
  set, no logs will be stored. If set to `-`, the logs will be sent to `stdout`.
- `DJANGO_SETTINGS_MODULE`: python path to settings file for the given environment, e.g. "app.settings.develop"
- `ALLOW_ADMIN_INITIATION_VIA_CLI`: Enables the `bootstrap` management command which creates default admin user,
  organisation, and project.
- `ADMIN_EMAIL`: Email to use for the default superuser creation.
- `ORGANISATION_NAME`: Organisation name to use for the default organisation.
- `PROJECT_NAME` Project name to use for the default project.
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
- `RESTRICT_ORG_CREATE_TO_SUPERUSERS`: Restricts all users from creating organisations unless they are
  [marked as a superuser](/deployment/configuration/django-admin#authentication).
- `FLAGSMITH_CORS_EXTRA_ALLOW_HEADERS`: Comma separated list of extra headers to allow when operating across domains.
  e.g. `'my-custom-header-1,my-custom-header-2'`. Defaults to `'sentry-trace,'`.
- `FLAGSMITH_DOMAIN`: A custom domain for URLs pointing to your Flagsmith instance in email notifications. Note: if set,
  the domain provided during [initial configuration](#environments-with-no-direct-console-access-eg-heroku-ecs) will be
  ignored.
- `DISABLE_FLAGSMITH_UI`: Disable the Flagsmith UI which can be rendered by the API containers in a single container
  environment. Use `True` to disable, defaults to `False`.
- `SEGMENT_CONDITION_VALUE_LIMIT`: Configure the size of the segment condition value in bytes. Default is 1000.
  Minimum 0. Maximum 2000000 (2MB). Note that this environment variable changes the length of the column in the database
  and hence should not be modified for already running instances of flagsmith. It should only be used for new
  installations, and should not be modified. WARNING: setting this to a higher limit may prevent imports to our SaaS
  platform if required in the future.
- `ENABLE_API_USAGE_TRACKING`: Enable tracking of all API requests in Postgres / Influx. Default is True. Setting to
  False will mean that the Usage tab in the Organisation Settings will not show any data. Useful when using Postgres for
  analytics in high traffic environments to limit the size of database.

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

### StatsD Integration

The application is run using python's gunicorn. As such, we are able to tell it to send statsd metrics to a given host
for monitoring purposes. Using our docker image, this can be done and configured by providing the following environment
variables.

- `STATSD_HOST`: the URL of the host that will collect the statsd metrics
- `STATSD_PORT`: optionally define the port on the host which is listening for statsd metrics (default: 8125)
- `STATSD_PREFIX`: optionally define a prefix for the statsd metrics (default: flagsmith.api)

Below is an example docker compose setup for using statsd with datadog. Note that it's important to set the
`DD_DOGSTATSD_NON_LOCAL_TRAFFIC` environment variable to `true` to ensure that your datadog agent is able to accept
metrics from external services.

```yaml
version: '3'
services:
 postgres:
  image: postgres:15.5-alpine
  environment:
   POSTGRES_PASSWORD: password
   POSTGRES_DB: flagsmith
  container_name: flagsmith_postgres
 api:
  build:
   dockerfile: Dockerfile
   context: ../../api
  environment:
   DATABASE_URL: postgres://postgres:password@postgres:5432/flagsmith
   DJANGO_SETTINGS_MODULE: app.settings.local
   STATSD_HOST: datadog
  ports:
   - '8000:8000'
  depends_on:
   - postgres
  links:
   - postgres
   - datadog
 datadog:
  image: gcr.io/datadoghq/agent:7
  environment:
   - DD_API_KEY=<API KEY>
   - DD_SITE=datadoghq.eu
   - DD_DOGSTATSD_NON_LOCAL_TRAFFIC=true
  volumes:
   - /var/run/docker.sock:/var/run/docker.sock
   - /proc/:/host/proc/:ro
   - /sys/fs/cgroup:/host/sys/fs/cgroup:ro
   - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

If not running our application via docker, you can find gunicorn's documentation on statsd instrumentation
[here](https://docs.gunicorn.org/en/stable/instrumentation.html)

## Caching

The application makes use of caching in a couple of locations:

1. Environment authentication - the application utilises caching for the environment object on all endpoints that use
   the X-Environment-Key header. By default, this is configured to use an in-memory cache. This can be configured using
   the options defined below.
2. Environment flags - the application utilises an in memory cache for the flags returned when calling /flags. The
   number of seconds this is cached for is configurable using the environment variable `"CACHE_FLAGS_SECONDS"`
3. Project Segments - the application utilises an in memory cache for returning the segments for a given project. The
   number of seconds this is cached for is configurable using the environment variable
   `"CACHE_PROJECT_SEGMENTS_SECONDS"`.
4. Flags and Identities endpoint caching - the application provides the ability to cache the responses to the GET /flags
   and GET /identities endpoints. The application exposes the configuration to allow the caching to be handled in a
   manner chosen by the developer. The configuration options are explained in more detail below.

### Flags & Identities endpoint caching

To enable caching on the flags and identities endpoints (GET requests only), you must set the following environment
variables:

| Environment Variable                                               | Description                                                                                                                    | Example value                                          | Default                                       |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | --------------------------------------------- |
| <code>GET\_[FLAGS&#124;IDENTITIES]\_ENDPOINT_CACHE_SECONDS</code>  | Number of seconds to cache the response to `GET /api/v1/flags`                                                                 | `60`                                                   | `0`                                           |
| <code>GET\_[FLAGS&#124;IDENTITIES]\_ENDPOINT_CACHE_BACKEND</code>  | Python path to the django cache backend chosen. See documentation [here](https://docs.djangoproject.com/en/3.2/topics/cache/). | `django.core.cache.backends.memcached.PyMemcacheCache` | `django.core.cache.backends.dummy.DummyCache` |
| <code>GET\_[FLAGS&#124;IDENTITIES]\_ENDPOINT_CACHE_LOCATION</code> | The location for the cache. See documentation [here](https://docs.djangoproject.com/en/3.2/topics/cache/).                     | `127.0.0.1:11211`                                      | `get_flags_endpoint_cache`                    |

An example configuration to cache both flags and identities requests for 30 seconds in a memcached instance hosted at
`memcached-container`:

```
GET_FLAGS_ENDPOINT_CACHE_SECONDS: 30
GET_FLAGS_ENDPOINT_CACHE_BACKEND: django.core.cache.backends.memcached.PyMemcacheCache
GET_FLAGS_ENDPOINT_CACHE_LOCATION: memcached-container:11211
GET_IDENTITIES_ENDPOINT_CACHE_SECONDS: 30
GET_IDENTITIES_ENDPOINT_CACHE_BACKEND: django.core.cache.backends.memcached.PyMemcacheCache
GET_IDENTITIES_ENDPOINT_CACHE_LOCATION: memcached-container:11211
```

### Environment authentication caching

On each request using the X-Environment-Key header, the flagsmith application retrieves the environment to perform the
relevant caching. This can be configured using environment variables to create a shared cache with a longer timeout. The
cache will be cleared automatically by certain actions in the platform when the environment changes.

| Environment Variable         | Description                                                                                                                    | Example value                                          | Default                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | --------------------------------------------- |
| `ENVIRONMENT_CACHE_SECONDS`  | Number of seconds to cache the environment for                                                                                 | `60`                                                   | `86400` ( = 24h)                              |
| `ENVIRONMENT_CACHE_BACKEND`  | Python path to the django cache backend chosen. See documentation [here](https://docs.djangoproject.com/en/3.2/topics/cache/). | `django.core.cache.backends.memcached.PyMemcacheCache` | `django.core.cache.backends.dummy.DummyCache` |
| `ENVIRONMENT_CACHE_LOCATION` | The location for the cache. See documentation [here](https://docs.djangoproject.com/en/3.2/topics/cache/).                     | `127.0.0.1:11211`                                      | `environment-objects`                         |

## Unified Front End and Back End Build

You can run Flagsmith as a single application/docker container using our unified builds. These are available on
[Docker Hub](https://hub.docker.com/repository/docker/flagsmith/flagsmith) but you can also run the front end as part of
the Django Application. Steps to do this:

```bash
# Update packages and build django.
cd frontend
npm install
npm run bundledjango

# Copy additional assets with Django
cd ../api
python manage.py collectstatic

# Boot the server
python manage.py runserver
```

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

We're using [Poetry](https://python-poetry.org/) to manage packages and dependencies, using Poetry standard workflows.
