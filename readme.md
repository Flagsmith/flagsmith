[<img alt="Feature Flag, Remote Config and A/B Testing platform, Flagsmith" width="100%" src="./hero.png"/>](https://flagsmith.com/)

[Flagsmith](https://www.flagsmith.com/) is an open source, fully featured, Feature Flag and Remote Config service. Use our hosted API, deploy to your own private cloud, or run on-premise.

# Flagsmith

Flagsmith makes it easy to create and manage features flags across web, mobile, and server side applications. Just wrap a section of code with a flag, and then use Flagsmith to toggle that feature on or off for different environments, users or user segments.

![Alt text](/screenshot.png?raw=true "Flagsmith")

## Features

* **Feature flags**. Release features with confidence through phased rollouts.
* **Remote config**. Easily toggle individual features on and off, and make changes without deploying new code.
* **A/B and Multivariate Testing**. Use segments to run A/B and multivariate tests on new features. With segments, you can also introduce beta programs to get early user feedback.
* **Organization Management**.  Organizations, projects, and roles for team members help keep your deployment organized.
* **Integrations**. Easily enhance Flagsmith with your favourite tools.

## Using Flagsmith

* **Flagsmith hosted**. You can try our hosted version for free at https://www.flagsmith.com/
* **Flagsmith open source**. The Flagsmith API is built using Python 3, Django 2, and DjangoRestFramework 3. You can begin running the open source application using docker-compose. We also have options fore deploying to AWS, Kubernetes and OpenShift.

## Resources

* [Website](https://www.flagsmith.com/)
* [Documentation](https://docs.flagsmith.com/)
* If you have any questions about our projects you can email [support@flagsmith.com](mailto:support@flagsmith.com)

# Flagsmith REST API

## Development Environment

Before running the application, you'll need to configure a database for the application. The steps 
to do this can be found in the following section entitled 'Databases'.  

```bash
virtualenv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python src/manage.py migrate
python src/manage.py runserver
```

The application can also be run locally using Docker Compose if required, however, it's beneficial 
to run locally using the above steps as it gives you hot reloading. To run using docker compose, 
simply run the following command from the project root:

```bash
docker-compose up
```

## Code Style

We are slowly migrating the code style to use [black](https://github.com/psf/black) as 
a formatter. Black automatically formats the code for you, you can run the formatter
by running:

```bash
python -m black path/to/directory/or/file.py
```

All new code should adhere to black formatting standards.

## Databases

Databases are configured in app/settings/\<env\>.py

The app is configured to use PostgreSQL for all environments.

When running locally, you'll need a local instance of postgres running. The easiest way to do this 
is to use docker which is achievable with the following command:

```docker run --name local_postgres -d -P postgres```

You'll also need to ensure that you have a value for POSTGRES_PASSWORD set as an environment 
variable on your development machine.

When running on a Heroku-ish platform, the application reads the database connection in production 
from an environment variable called `DATABASE_URL`. This should be configured in the Heroku-ish 
application configuration.

When running the application using Docker, it reads the database configuration from the settings 
located in `app.settings.master-docker`

## Initialising

### Locally

The application is built using django which comes with a handy set of admin pages available at 
`/admin/`. To access these, you'll need to create a super user. This can be done with the following
command:

```bash
python src/manage.py createsuperuser
```

Once you've created the super user, you can use the details to log in at `/admin/`. From here, you 
can create an organisation and either create another user or simply assign the organisation to your
admin user to begin using the application. 

### In a Heroku-ish environment

Once the app has been deployed, you can initialise it to create a super user by sending a GET request 
to  the `/api/v1/users/init/` endpoint. This will create a super user with the details configured in 
`app.settings.common` with the following parameters: 

```
ADMIN_USERNAME,
ADMIN_EMAIL,
ADMIN_INITIAL_PASSWORD
``` 

Note that this functionality can be turned off in the settings if required by setting 
`ALLOW_ADMIN_INITIATION_VIA_URL=False`. 

## Deploying

### Using Heroku-ish Platform (e.g. Heroku, Dokku, Flynn)

The application should run on any Heroku-ish platform (e.g. Dokku, Flynn) by simply adding the 
required git repo and pushing the code. The code for running the app is contained in the Procfile.

To get it running, you'll need to add the necessary config variables as outlined below.

### Using ElasticBeanstalk

The application will run within ElasticBeanstalk using the default Python setup.
We've included the .ebextensions/ and .elasticbeanstalk/ directories which will run on ElasticBeanstalk.

The changes required to run in your environment will be as follows

`.elasticbeanstalk/config.yml` - update application_name and default_region to the relevant variables for your setup.

`.ebextensions/options.config` - within the root of the project `generate.sh` will add in all environment variables that are required using your chosen CI/CD. Alternatively, you can add your own `options.config`.

### Using Docker

The application can be configured to run using docker with simply by running the following command:

```bash
docker-compose up
```

This will use some default settings created in the `docker-compose.yml` file located in the root of 
the project. These should be changed before using in any production environments.

You can work on the project itself using Docker:

```bash
docker-compose -f docker-compose.dev.yml up
```

This gets an environment up and running along with Postgres and enables hot reloading etc. 

### Environment Variables

The application relies on the following environment variables to run:

* `ENV`: string representing the current running environment, e.g. 'local', 'dev', 'prod'. Defaults to 'local'
* `DJANGO_ALLOWED_HOSTS`: comma separated list of hosts the application will run on in the given environment
* `DJANGO_CSRF_TRUSTED_ORIGINS`: comma separated list of hosts to allow unsafe (POST, PUT) requests from. Useful for allowing localhost to set traits in development.
* `DJANGO_SETTINGS_MODULE`: python path to settings file for the given environment, e.g. "app.settings.develop"
* `DJANGO_SECRET_KEY`: secret key required by Django, if one isn't provided one will be created using `django.core.management.utilsget_random_secret_key`
* `EMAIL_BACKEND`: email provider. Allowed values are `sgbackend.SendGridBackend` for Sendgrid or `django_ses.SESBackend` for Amazon SES. Defaults to `sgbackend.SendGridBackend`.
* `SENDGRID_API_KEY`: API key for the Sendgrid account
* `SENDER_EMAIL`: Email address from which emails are sent
* `AWS_SES_REGION_NAME`: If using Amazon SES as the email provider, specify the region (e.g. eu-central-1) that contains your verified sender e-mail address. Defaults to us-east-1
* `AWS_SES_REGION_ENDPOINT`: ses region endpoint, e.g. email.eu-central-1.amazonaws.com. Required when using ses in a region other than us-east-1
* `AWS_ACCESS_KEY_ID`: If using Amazon SES, these form part of your SES credentials.
* `AWS_SECRET_ACCESS_KEY`: If using Amazon SES, these form part of your SES credentials.
* `DATABASE_URL`: required by develop and master environments, should be a standard format database url e.g. postgres://user:password@host:port/db_name
* `DJANGO_SECRET_KEY`: see 'Creating a secret key' section below
* `GOOGLE_ANALYTICS_KEY`: if google analytics is required, add your tracking code
* `GOOGLE_SERVICE_ACCOUNT`: service account json for accessing the google API, used for getting usage of an organisation - needs access to analytics.readonly scope
* `INFLUXDB_TOKEN`: If you want to send API events to InfluxDB, specify this write token.
* `INFLUXDB_URL`: The URL for your InfluxDB database
* `INFLUXDB_ORG`: The organisation string for your InfluxDB API call.
* `GA_TABLE_ID`: GA table ID (view) to query when looking for organisation usage
* `AWS_STORAGE_BUCKET_NAME`: bucket name to store static files. Required if `USE_S3_STORAGE' is true.
* `AWS_S3_REGION_NAME`: region name of the static files bucket. Defaults to eu-west-2.
* `ALLOWED_ADMIN_IP_ADDRESSES`: restrict access to the django admin console to a comma separated list of IP addresses (e.g. `127.0.0.1,127.0.0.2`) 
* `USER_CREATE_PERMISSIONS`: set the permissions for creating new users, using a comma separated list of djoser or rest_framework permissions. Use this to turn off public user creation for self hosting. e.g. `'djoser.permissions.CurrentUserOrAdmin'` Defaults to `'rest_framework.permissions.AllowAny'`.
* `ENABLE_EMAIL_ACTIVATION`: new user registration will go via email activation flow, default False
* `SENTRY_SDK_DSN`: If using Sentry, set the project DSN here.
* `SENTRY_TRACE_SAMPLE_RATE`: Float. If using Sentry, sets the trace sample rate. Defaults to 1.0.

## Pre commit

The application uses pre-commit configuration ( `.pre-commit-config.yaml` ) to run black formatting before commits.

To install pre-commit:

```bash
pip install pre-commit
pre-commit install
```

### Creating a secret key

It is important to also set an environment variable on whatever platform you are using for 
`DJANGO_SECRET_KEY`. There is a function to create one in `app.settings.common` if none exists in 
the environment variables, however, this is not suitable for use in production. To generate a new 
secret key, you can use the function defined in `src/secret-key-gen.py` by simply running it from a 
command prompt:

```bash
python secret-key-gen.py
```

## Adding dependencies

To add a python dependency, add it to requirements.txt / requirements-dev.txt with it's current version number. 

## Caching

The application makes use of caching in a couple of locations:

1. Environment authentication - the application utilises an in memory cache for the environment object 
on all endpoints that use the X-Environment-Key header. 
2. Environment flags - the application utilises an in memory cache for the flags returned when calling 
/flags. The number of seconds this is cached for is configurable using the environment variable 
`"CACHE_FLAGS_SECONDS"`
3. Project Segments - the application utilises an in memory cache for returning the segments for a 
given project. The number of seconds this is cached for is configurable using the environment variable
`"CACHE_PROJECT_SEGMENTS_SECONDS"`.

## Stack

- Python 3.8
- Django 2.2.17
- DjangoRestFramework 3.12.1

## Static Files

Although the application relies on very few static files, it is possible to optimise their configuration to 
host these static files in S3. This is done using the relevant environment variables provided above. Note, however, 
that in order to use the configuration, the environment that you are hosting on must have the correct AWS credentials
configured. This can be done using environment variables or, in the case of AWS hosting such as Elastic Beanstalk, 
you can add the correct permissions to the EC2 Role. The role will need full access to the specific bucket 
that the static files are hosted in.

## Documentation

Further documentation can be found [here](https://docs.bullet-train.io).

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/kyle-ssg/c36a03aebe492e45cbd3eefb21cb0486) 
for details on our code of conduct, and the process for submitting pull requests to us.

## Getting Help

If you encounter a bug or feature request we would like to hear about it. Before you submit an
issue please search existing issues in order to prevent duplicates.

## Get in touch

If you have any questions about our projects you can email
<a href="mailto:support@flagsmith.com">support@flagsmith.com</a>.

## Useful links

[Website](https://www.flagsmith.com)

[Product Roadmap](https://product-hub.io/roadmap/5d81f2406180537538d99f28)

[Documentation](https://docs.flagsmith.com/)

[Code Examples](https://github.com/Flagsmith/flagsmith-train-examples)

[Youtube Tutorials](https://www.youtube.com/channel/UCki7GZrOdZZcsV9rAIRchCw)
