---
title: Deploying Flagsmith on Google Cloud
sidebar_label: Google Cloud
sidebar_position: 75
---

## Overview

We recommend running Flagsmith on Google Cloud Platform using the following services:

- [Cloud Run](https://cloud.google.com/run) for the application server
- [Cloud SQL/Postgres](https://cloud.google.com/sql/postgresql) for the database

## Cloud Run

Unless you have specific requirements, we recommend running the
[unified Docker image](https://hub.docker.com/repository/docker/flagsmith/flagsmith).

It's best to study our [docker-compose file](https://github.com/Flagsmith/self-hosted/blob/main/docker-compose.yml) in
order to set up the base environment variables. Further environment variables are
[described here](locally-api.md#environment-variables).

Run a single Cloud Run service with at least two container instances running for failover. For more info on sizing, see
our [scaling page](/deployment/configuration/sizing-and-scaling). We recommend running with at least
[2 minimum instances](https://cloud.google.com/run/docs/configuring/min-instances) to avoid cold starts particularly in
order to serve low-latency requests to the SDKs.

If you are using health-checks, make sure to use `/health` as the health-check endpoint for both the API and the Front
End.

## Cloud SQL/Postgres

We support Postgres versions `11+`. Our SaaS platform runs in production on PostgreSQL version `11`. When starting for
the first time, the application will create that database schema automatically. Schema upgrades will also happen
seamlessly during application server upgrades.
