---
title: Aptible
---

## Prerequisites

The options and health check routes described in this document are available from Flagsmith 2.130.0.

## Configuration

Running Flagsmith on Aptible requires some configuration tweaks because of how Aptible's application lifecycle works:

- Don't wait for the database to be available before the Flagsmith API starts. You can do this by setting the
  `SKIP_WAIT_FOR_DB` environment variable.
- Add `containers` as an allowed host to comply with Aptible's
  [strict health checks](https://www.aptible.com/docs/core-concepts/apps/connecting-to-apps/app-endpoints/https-endpoints/health-checks#strict-health-checks).
- Use the `before_release` tasks from `.aptible.yml` to run database migrations
- Use a Procfile to only start the API and not perform database migrations on startup

This configuration can be applied by adding the Procfile and `.aptible.yml` configuration files to a
[Docker image](https://www.aptible.com/docs/core-concepts/apps/deploying-apps/image/deploying-with-docker-image/overview#how-do-i-deploy-from-docker-image)
that you build starting from a Flagsmith base image:

```text title="Procfile"
cmd: serve
```

```yaml title=".aptible.yml"
before_release:
 - migrate
 - bootstrap
```

```dockerfile title="Dockerfile"
# Use flagsmith/flagsmith-private-cloud for the Enterprise image
FROM --platform=linux/amd64 flagsmith/flagsmith

# Don't wait for the database to be available during startup for health checks to succeed
ENV SKIP_WAIT_FOR_DB=1

# Use root user to add Aptible files to the container
USER root
RUN mkdir /.aptible/
ADD Procfile /.aptible/Procfile
ADD .aptible.yml /.aptible/.aptible.yml

# Use non-root user at runtime
USER nobody
```

Before deploying, set the environment variables for your database URL and allowed hosts from the Aptible dashboard, or
using the Aptible CLI:

```shell
aptible config:set --app flagsmith \
    DATABASE_URL=postgresql://aptible:...@...:23532/db \
    DJANGO_ALLOWED_HOSTS='containers,YOUR_APTIBLE_HOSTNAME'
```

## Deployment

After your image is built and pushed to a container registry that Aptible can access, you can deploy it using the
Aptible CLI as you would any other application:

```shell
aptible deploy --app flagsmith --docker-image example/my-flagsmith-aptible-image
```

Once Flagsmith is running in Aptible, make sure to create the first admin user by visiting `/api/v1/users/config/init/`.
