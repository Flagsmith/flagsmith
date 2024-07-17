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

For example, if your Aptible app is named `flagsmith`, you could set its configuration using the Aptible CLI:

```shell
aptible config:set --app flagsmith\
    DATABASE_URL=postgresql://aptible:...@db-shared-us-west-1-132662.aptible.in:23532/db \
    SKIP_WAIT_FOR_DB=1 \
    DJANGO_ALLOWED_HOSTS='["containers", "your_aptible_hostname"]'
```

Once Flagsmith is running in Aptible, make sure to create the first admin user by visiting `/api/v1/users/config/init/`.

## Optional: using a `Procfile` or `.aptible.yml`

If your Aptible deployment requires a
[configuration file](https://www.aptible.com/docs/core-concepts/apps/deploying-apps/image/deploying-with-docker-image/procfile-aptible-yml-direct-docker-deploy)),
you can build it into a new container image starting from a Flagsmith base image. For example, if you wanted to add a
`Procfile` to the Flagsmith image:

```dockerfile
# Use flagsmith/flagsmith-private-cloud for the Enterprise image
FROM --platform=linux/amd64 flagsmith/flagsmith
USER root
RUN mkdir /.aptible/
ADD Procfile /.aptible/Procfile
```

After your image is deployed and pushed to a container registry that Aptible can access, you can deploy it using the
Aptible CLI as you would any other application:

```shell
aptible deploy --app flagsmith --docker-image example/my-flagsmith-aptible-image
```
