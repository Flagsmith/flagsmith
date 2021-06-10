[<img alt="Feature Flag, Remote Config and A/B Testing platform, Flagsmith" width="100%" src="./hero.png"/>](https://flagsmith.com/)

[Flagsmith](https://www.flagsmith.com/) is an open source, fully featured, Feature Flag and Remote Config service. Use
our hosted API, deploy to your own private cloud, or run on-premise.

# Flagsmith

Flagsmith makes it easy to create and manage features flags across web, mobile, and server side applications. Just wrap
a section of code with a flag, and then use Flagsmith to toggle that feature on or off for different environments, users
or user segments.

<img alt="Flagsmith Screenshot" width="100%" src="./screenshot.png"/>

## Features

- **Feature flags**. Release features with confidence through phased rollouts.
- **Remote config**. Easily toggle individual features on and off, and make changes without deploying new code.
- **A/B and Multivariate Testing**. Use segments to run A/B and multivariate tests on new features. With segments, you
  can also introduce beta programs to get early user feedback.
- **Organization Management**. Organizations, projects, and roles for team members help keep your deployment organized.
- **Integrations**. Easily enhance Flagsmith with your favourite tools.

## Using Flagsmith

- **Flagsmith hosted**. You can try our hosted version for free at https://www.flagsmith.com/
- **Flagsmith open source**. The Flagsmith API is built using Python 3, Django 2, and DjangoRestFramework 3. You can
  begin running the open source application using docker-compose. We also have options fore deploying to AWS, Kubernetes
  and OpenShift.

## Resources

- [Website](https://www.flagsmith.com/)
- [Documentation](https://docs.flagsmith.com/)
- If you have any questions about our projects you can email [support@flagsmith.com](mailto:support@flagsmith.com)

# Flagsmith REST API

## Development Environment

Before running the application, you'll need to configure a database for the application. The steps to do this can be
found in the following section entitled 'Databases'.

```bash
virtualenv .venv
source .venv/bin/activate
pip install pip-tools
pip-sync requirements.txt requirements-dev.txt
python src/manage.py migrate
python src/manage.py runserver
```

Note: if you're running on on MacOS and you find some issues installing the dependencies (specifically around pyre2),
you may need to run the following:

```bash
brew install cmake re2
```

The application can also be run locally using Docker Compose if required, however, it's beneficial to run locally using
the above steps as it gives you hot reloading. To run using docker compose, simply run the following command from the
project root:

```bash
docker-compose up
```

## Databases

Databases are configured in app/settings/\<env\>.py

The app is configured to use PostgreSQL for all environments.

When running locally, you'll need a local instance of postgres running. The easiest way to do this is to use docker
which is achievable with the following command:

`docker run --name local_postgres -d -P postgres`

You'll also need to ensure that you have a value for POSTGRES_PASSWORD set as an environment variable on your
development machine.

When running on a Heroku-ish platform, the application reads the database connection in production from an environment
variable called `DATABASE_URL`. This should be configured in the Heroku-ish application configuration.

When running the application using Docker, it reads the database configuration from the settings located in
`app.settings.production`

## Initialising

### Locally

The application is built using django which comes with a handy set of admin pages available at `/admin/`. To access
these, you'll need to create a super user. This can be done with the following command:

```bash
python src/manage.py createsuperuser
```

Once you've created the super user, you can use the details to log in at `/admin/`. From here, you can create an
organisation and either create another user or simply assign the organisation to your admin user to begin using the
application.

### In a Heroku-ish environment

Once the app has been deployed, you can initialise it to create a super user by sending a GET request to the
`/api/v1/users/init/` endpoint. This will create a super user with the details configured in `app.settings.common` with
the following parameters:

```bash
ADMIN_USERNAME,
ADMIN_EMAIL,
ADMIN_INITIAL_PASSWORD
```

Note that this functionality can be turned off in the settings if required by setting
`ALLOW_ADMIN_INITIATION_VIA_URL=False`.

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
[Flagsmith Docker repository](https://github.com/Flagsmith/flagsmith-docker).

The application can be configured to run using docker with simply by running the following command:

```bash
docker-compose up
```

This will use some default settings created in the `docker-compose.yml` file located in the root of the project. These
should be changed before using in any production environments.

You can work on the project itself using Docker:

```bash
docker-compose -f docker-compose.dev.yml up
```

This gets an environment up and running along with Postgres and enables hot reloading etc.

The docker container also accepts an argument that sets the access log file location for gunicorn. By default this is
set to /dev/null to maintain the default behaviour of gunicorn. It can either be set to `"-"` to redirect the logs to
stdout or to a location on the file system as required.

### Environment Variables

The application relies on the following environment variables to run:

#### Database Environment Variables

- `DATABASE_URL`: required by develop and master environments, should be a standard format database url e.g.
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
- `DJANGO_ALLOWED_HOSTS`: comma separated list of hosts the application will run on in the given environment
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma separated list of hosts to allow unsafe (POST, PUT) requests from. Useful for
  allowing localhost to set traits in development.
- `DJANGO_SETTINGS_MODULE`: python path to settings file for the given environment, e.g. "app.settings.develop"
- `GOOGLE_ANALYTICS_KEY`: if google analytics is required, add your tracking code
- `GOOGLE_SERVICE_ACCOUNT`: service account json for accessing the google API, used for getting usage of an
  organisation - needs access to analytics.readonly scope
- `INFLUXDB_TOKEN`: If you want to send API events to InfluxDB, specify this write token.
- `INFLUXDB_URL`: The URL for your InfluxDB database
- `INFLUXDB_ORG`: The organisation string for your InfluxDB API call.
- `GA_TABLE_ID`: GA table ID (view) to query when looking for organisation usage
- `ALLOWED_ADMIN_IP_ADDRESSES`: restrict access to the django admin console to a comma separated list of IP addresses
  (e.g. `127.0.0.1,127.0.0.2`)
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

#### Email Environment Variables

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
- `AWS_SES_REGION_ENDPOINT`: ses region endpoint, e.g. email.eu-central-1.amazonaws.com. Required when using ses in a
  region other than us-east-1
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

It is important to also set an environment variable on whatever platform you are using for `DJANGO_SECRET_KEY`. There is
a function to create one in `app.settings.common` if none exists in the environment variables, however, this is not
suitable for use in production. To generate a new secret key, you can use the function defined in
`src/secret-key-gen.py` by simply running it from a command prompt:

```bash
python secret-key-gen.py
```

## Pre commit

The application uses pre-commit configuration ( `.pre-commit-config.yaml` ) to run black formatting before commits.

To install pre-commit:

```bash
pip install pre-commit
pre-commit install
```

You can manually run the black formatter with:

```bash
python -m black src
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

To add a new library to the project, edit requirements.in amd then:

```bash
pip-compile requirements.in
pip install -r requirements.txt
```

## Documentation

Further documentation can be found [here](https://docs.flagsmith.com/).

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/kyle-ssg/c36a03aebe492e45cbd3eefb21cb0486) for details on our code
of conduct, and the process for submitting pull requests to us.

## Getting Help

If you encounter a bug or feature request we would like to hear about it. Before you submit an issue please search
existing issues in order to prevent duplicates.

## Get in touch

If you have any questions about our projects you can email
<a href="mailto:support@flagsmith.com">support@flagsmith.com</a>.

## Useful links

[Website](https://www.flagsmith.com)

[Product Roadmap](https://product-hub.io/roadmap/5d81f2406180537538d99f28)

[Documentation](https://docs.flagsmith.com/)

[Code Examples](https://github.com/Flagsmith/flagsmith-train-examples)

[Youtube Tutorials](https://www.youtube.com/channel/UCki7GZrOdZZcsV9rAIRchCw)
