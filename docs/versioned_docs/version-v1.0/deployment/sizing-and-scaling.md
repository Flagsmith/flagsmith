---
title: Sizing and Scaling
description: Sizing and Scaling Flagsmith
sidebar_position: 80
---

## Overview

Flagsmith has a very simple architecture, making it well understood when it comes to serving high loads.

## Frontend Dashboard

Generally this component is not put under any sort of significant load. It can be load balanced if required. It does not
require sticky-sessions.

## API

The API is completely stateless. This means it can scale out behind a load balancer almost perfectly. As an example,
when running on AWS ECS/Fargate we run with:

- `cpu=1024`
- `memory=2048`

In terms of auto scaling, we recommend basing the autoscaling off the `ECSServiceAverageCPUUtilization` metric, with a
`target_value` of `50` and a 30 second cool-down timeout.

## Database

Our recommendation is to first scale the database up with a more powerful single server.

Once the database connections have been saturated by the API cluster, adding read replicas to the database solves the
next bottleneck of database connections.

We would also recommend testing [pgBouncer](https://www.pgbouncer.org/) in your environment as it generally optimises
database connections and reduces the load on the database.
