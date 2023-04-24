---
description: Getting Started with Flagsmith on Docker
sidebar_position: 40
---

# Docker

You can use docker to set up an entire [Flagsmith Feature Flag](https://www.flagsmith.com) environment locally. Just
clone the [docker repository](https://github.com/Flagsmith/self-hosted) and run docker-compose:

```bash
git clone https://github.com/Flagsmith/self-hosted.git
cd self-hosted
docker-compose up
```

Wait for the images to download and run, then visit `http://localhost:8000/`. As a first step, you will need to create a
new account at [http://localhost:8000/signup](http://localhost:8000/signup)

## Environment Variables

As well as the Environment Variables specified in the [API](/deployment/hosting/locally-api#environment-variables) and
[Front End](/deployment/hosting/locally-frontend#environment-variables) you can also specify the following:

- `GUNICORN_WORKERS`: The number of [Gunicorn Workers](https://docs.gunicorn.org/en/stable/settings.html#workers) that
  are created
- `GUNICORN_THREADS`: The number of
  [Gunicorn Threads per Worker](https://docs.gunicorn.org/en/stable/settings.html#threads)
- `GUNICORN_TIMEOUT`: The number of seconds before the
  [Gunicorn times out](https://docs.gunicorn.org/en/stable/settings.html#timeout)
- `ACCESS_LOG_LOCATION`: The location to write access logs to

## Platform Architectures

Our Docker images are built against the following CPU architectures:

- `amd64`
- `linux/arm64`
- `linux/arm/v7`

## Architecture

The docker-compose file runs the following containers:

### Front End Dashboard and REST API combined - Port 8000

The Web user interface allows you to create accounts and manage your flags. The front end is written in node.js and
React.

The web user interface communicates via REST to the API that powers the application. The SDK clients also connect to
this API. The API is written in Django and the Django REST Framework.

Once you have created an account and some flags, you can then start using the API with one of the
[Flagsmith Client SDKs](https://github.com/Flagsmith?q=client&type=&language=). You will need to override the API
endpoint for each SDK to point to [http://localhost:8000/api/v1/](http://localhost:8000/api/v1/).

You can access the Django Admin console to get CRUD access to some of the core tables within the API. You will need to
create a super user account first with the following command:

```bash
# Make sure you are in the root directory of this repository
docker-compose run --rm --entrypoint "python manage.py createsuperuser" api
```

You can then access the admin dashboard at [http://localhost:8000/admin/](http://localhost:8000/admin/)

### Postgres Database

The REST API stores all its data within a Postgres database. Schema changes will be carried out automatically when
upgrading using Django Migrations.

## Access Flagsmith Remotely

You will need to either open ports into your docker host or set up a reverse proxy to access the two Flagsmith services
(dashboard and API). You will also need to configure the dashboard environment variable `API_URL`, which tells the
dashboard where the REST API is located.
