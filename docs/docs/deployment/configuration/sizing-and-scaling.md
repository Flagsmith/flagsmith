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

### Replication

Once the database connections have been saturated by the API cluster, adding read replicas to the database solves the
next bottleneck of database connections.

Flagsmith can be set up to handle as many read replicas as needed. To add replicas, you'll need to set the
`REPLICA_DATABASE_URLS` environment variable with a comma separated list of database urls.

Example:

```
REPLICA_DATABASE_URLS: postgres://user:password@replica1.database.host:5432/flagsmith,postgres://user:password@replica2.database.host:5432/flagsmith
```

:::tip

Use the `REPLICA_DATABASE_URLS_DELIMITER` environment variable if you are using any `,` characters in your passwords.

:::

In addition to typical read replicas, which usually exist locally in the same data centre to the application. There is
also support for replicas across regions via the `CROSS_REGION_REPLICA_DATABASE_URLS` environment variable which is set
in the same way as the `REPLICA_DATABASE_URLS` with cross region replicas having their own matching
CROSS_REGION_REPLICA_DATABASE_URLS_DELIMITER which also defaults to `,` as above.

Cross region replicas are only used once all typical replicas have gone offline, since the performance characteristics
wouldn't be favorable to spread replica load at longer latencies. Both `REPLICA_DATABASE_URLS` and
`CROSS_REGION_REPLICA_DATABASE_URLS` can be used alone or simultaneously.

To support different configurations there are two different replication strategies available. By setting
`REPLICA_READ_STRATEGY` to `DISTRIBUTED` (the default option) the load to the replicas is distributed evenly. If your
use-case, on the otherhand, is to utilize fallback replicas (primary, secondary, etc) the `REPLICA_READ_STRATEGY` should
be set to `SEQUENTIAL` so a replica is only used if all the other replica's preceding it have gone offline. This
strategy is applicable to both typical replicas as well as to cross region replicas.

We would also recommend testing [pgBouncer](https://www.pgbouncer.org/) in your environment as it generally optimises
database connections and reduces the load on the database.
