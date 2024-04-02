---
title: Data Migration
sidebar_position: 110
---

The data migration option is useful when you want to migrate your Flagsmith application from one location to another.
It's not a useful tool to merge Flagsmith data into another Flagsmith instance, for that use-case consider
[feature flag importing](/system-administration/importing-and-exporting/features).

If, for example, you wanted to move from self hosting Flagsmith to our SaaS version, the process looks something like
this:

- **Step 1.** Contact Flagsmith support to confirm you would like to migrate from self hosted to cloud
- **Step 2.** Generate a JSON file from your self hosted instance (more information below)
- **Step 3.** Send the JSON file to Flagsmith support
- **Step 4.** Flagsmith support will import the JSON file into our cloud offering
- **Step 5.** Register and re-add your users and passwords (Flagsmith support will need to assign at least one
  organisation administrator to the newly imported organisation)

## What is exported?

We **will** export the following entities:

- Flags
- Segments
- Identities
- Integrations

We **will not** export the following entities:

- Flagsmith Users that log into the Dashboard and manage Flagsmith
- Audit logs
- Change requests
- Scheduled flag changes

## Exporting

:::info

Please contact us if you need to be sent an export of your Organisation from our SaaS platform.

:::

The export process involves running a command from a terminal window. This must either be run from a running container
in your self hosted deployment or, alternatively, you can run a separate container that can connect to the same database
as your deployed fleet of flagsmith instances. To run the command, you'll also need to find the id of your organisation.
You can do this through the django admin interface. Information about accessing the admin interface can be found
[here](/deployment/configuration/django-admin.md). Once you've obtained access to the admin interface, if you browse to
the 'Organisations' menu item on the left, you should see something along the lines of the following:

![](/img/organisations-admin.png)

The ID you need is the one in brackets after the organisation name, so here it would be 1.

Once you've obtained the ID of your organisation, you're ready to export the organisation as a JSON file. There are 2
options as to where to output the organisation export JSON file. Option 1 - local file system, Option 2 - S3 bucket.
These options are detailed below.

### Option 1 - Local File System

```bash
python manage.py dumporganisationtolocalfs <organisation-id> <local-file-system-path>
```

e.g.

```bash
python manage.py dumporganisationtolocalfs 1 /tmp/organisation-1.json
```

Since this will write to your local file system, you may need to attach a volume to your docker container to be able to
obtain the file afterwards. There is an example docker-compose file provided below to help guide you to do this.

```yml
version: '3'
services:
 postgres:
  image: postgres:15.5-alpine
  environment:
   POSTGRES_PASSWORD: password
   POSTGRES_DB: flagsmith
  container_name: flagsmith_postgres
  ports:
   - '5434:5432'

 flagsmith:
  build:
   dockerfile: ./Dockerfile
   context: .
  environment:
   DJANGO_ALLOWED_HOSTS: '*'
   DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
   ENV: prod
   ALLOW_REGISTRATION_WITHOUT_INVITE: 'True'
  ports:
   - '8000:8000'
  depends_on:
   - postgres
  links:
   - postgres

 flagsmith-fs-exporter:
  build:
   dockerfile: ./Dockerfile
   context: .
  environment:
   DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
  command:
   - 'dump-organisation-to-local-fs'
   - '1'
   - '/tmp/flagsmith-exporter/org-1.json'
  depends_on:
   - postgres
   - flagsmith
  links:
   - postgres
  volumes:
   - '/tmp/flagsmith-exporter:/tmp/flagsmith-exporter'
```

### Option 2 - S3 bucket

The command you will need to run for this is slightly different as per the following.

```bash
python manage.py dumporganisationtos3 <organisation-id> <bucket-name> <key>
```

e.g.

```bash
python manage.py dumporganisationtos3 1 my-export-bucket exports/organisation-1.json
```

This requires the application to be running with access to an AWS account. If you're running the application in AWS,
make sure whichever role you are using to run you container has access to read from and write to the given S3 bucket.
Alternatively, you can provide the `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` environment variables to refer to an
IAM user that has access to the S3 bucket.

#### Using localstack to achieve local/test exports with s3 can be done using

[localstack](https://github.com/localstack/localstack) and the
[service-specific endpoint](https://docs.aws.amazon.com/sdkref/latest/guide/feature-ss-endpoints.html) strategy.

Once running you are able to set a specific url for the s3 service `AWS_ENDPOINT_URL_S3` or for all services
`AWS_ENDPOINT_URL`.

## Importing

### Option 1 - Local File System

This is coming soon - see https://github.com/Flagsmith/flagsmith/issues/2512 for more info.

### Option 2 - S3 bucket

```bash
python manage.py import-organisation-from-s3 <bucket-name> <key>
```

e.g.

```bash
python manage.py import-organisation-from-s3 my-export-bucket exports/organisation-1.json
```

#### Using localstack to achieve local/test imports with s3 can be done using

[localstack](https://github.com/localstack/localstack) and the
[service-specific endpoint](https://docs.aws.amazon.com/sdkref/latest/guide/feature-ss-endpoints.html) strategy.

Once running you are able to set a specific url for the s3 service `AWS_ENDPOINT_URL_S3` or for all services
`AWS_ENDPOINT_URL`.
