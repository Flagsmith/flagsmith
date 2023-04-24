---
title: Deploying Flagsmith on AWS
description: Getting Started with Flagsmith on AWS
sidebar_label: AWS
sidebar_position: 70
---

## Overview

We recommend running Flagsmith on AWS using the following AWS services:

- ECS/Fargate for running the Docker image
- RDS/Aurora/Postgres for the database
- Application Load Balancer to distribute traffic

We have [Pulumi](https://www.pulumi.com/) scripts available for AWS deployments. Please get in touch if these are of
interest.

## ECS

Unless you have specific requirements, we recommend running the
[unified Docker image](https://hub.docker.com/repository/docker/flagsmith/flagsmith).

It's best to study our [docker-compose file](https://github.com/Flagsmith/self-hosted/blob/main/docker-compose.yml) in
order to set up the base environment variables. Further environment variables are
[described here](locally-api.md#environment-variables).

Run a single ECS service with at least two Fargate instances running for failover. For more info on Fargate sizes, see
our [scaling page](/deployment/configuration/sizing-and-scaling).

If you are using health-checks, make sure to use `/health` as the health-check endpoint.

## RDS/Aurora

We run in production on PostgreSQL version `11`; Aurora release `3.x`. When starting for the first time, the application
will create that database schema automatically. Schema upgrades will also happen seamlessly during application server
upgrades.

## Application Load Balancer

We direct all traffic through an AWS ALB to the relevant ECS service.
