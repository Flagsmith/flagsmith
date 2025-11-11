---
title: Using InfluxDB for Analytics
description: How to offload time-series data to InfluxDB instead of PostgreSQL.
---

Flagsmith has a soft dependency on InfluxDB to store time-series data. You don't need to configure InfluxDB to run the platform; by default, this data will be stored in PostgreSQL. If you are running very high traffic loads, you might be interested in deploying InfluxDB.

## Docker

1. Create a user account in InfluxDB. You can visit [http://localhost:8086/]
2. Go into Data > Buckets and create three new buckets called `default`, `default_downsampled_15m` and
   `default_downsampled_1h`
3. Go into Data > Tokens and grab your access token.
4. Edit the `docker-compose.yml` file and add the following `environment` variables in the API service to connect the API to InfluxDB:
   - `INFLUXDB_TOKEN`: The token from the step above
   - `INFLUXDB_URL`: `http://influxdb`
   - `INFLUXDB_ORG`: The organisation ID - you can find it
     [here](https://docs.influxdata.com/influxdb/v2.0/organizations/view-orgs/)
   - `INFLUXDB_BUCKET`: `default`
5. Restart `docker-compose`
6. Create a new task with the following query. This will downsample your per-millisecond API request data down to 15-minute blocks for faster queries. Set it to run every 15 minutes.

```text
option task = {name: "Downsample (API Requests)", every: 15m}

data = from(bucket: "default")
 |> range(start: -duration(v: int(v: task.every) * 2))
 |> filter(fn: (r) =>
  (r._measurement == "api_call"))

data
 |> aggregateWindow(fn: sum, every: 15m)
 |> filter(fn: (r) =>
  (exists r._value))
 |> to(bucket: "default_downsampled_15m")
```

Once this task has run, you will see data coming into the Organisation API Usage area.

7. Create another new task with the following query. This will downsample your per-millisecond flag evaluation data down to 15-minute blocks for faster queries. Set it to run every 15 minutes.

```text
option task = {name: "Downsample (Flag Evaluations)", every: 15m}

data = from(bucket: "default")
 |> range(start: -duration(v: int(v: task.every) * 2))
 |> filter(fn: (r) =>
  (r._measurement == "feature_evaluation"))

data
 |> aggregateWindow(fn: sum, every: 15m)
 |> filter(fn: (r) =>
  (exists r._value))
 |> to(bucket: "default_downsampled_15m")
```

Once this task has run, and you have made some flag evaluations with analytics enabled (see documentation [here](/managing-flags/flag-analytics) for information on this), you should see data in the 'Analytics' tab against each feature in your dashboard.

8. Create another new task with the following query. This will downsample your per-millisecond API request data down to 1-hour blocks for faster queries. Set it to run every 1 hour.

```text
option task = {name: "Downsample API 1h", every: 1h}

data = from(bucket: "default")
 |> range(start: -duration(v: int(v: task.every) * 2))
 |> filter(fn: (r) =>
  (r._measurement == "api_call"))

data
 |> aggregateWindow(fn: sum, every: 1h)
    |> filter(fn: (r) =>
      (exists r._value))
 |> to(bucket: "default_downsampled_1h")
```

9. Create another new task with the following query. This will downsample your per-millisecond flag evaluation data down to 1-hour blocks for faster queries. Set it to run every 1 hour.

```text
option task = {name: "Downsample API 1h - Flag Analytics", every: 1h}

data = from(bucket: "default")
 |> range(start: -duration(v: int(v: task.every) * 2))
 |> filter(fn: (r) =>
  (r._measurement == "feature_evaluation"))
 |> filter(fn: (r) =>
  (r._field == "request_count"))
 |> group(columns: ["feature_id", "environment_id"])

data
 |> aggregateWindow(fn: sum, every: 1h)
    |> filter(fn: (r) =>
      (exists r._value))
 |> set(key: "_measurement", value: "feature_evaluation")
 |> set(key: "_field", value: "request_count")
 |> to(bucket: "default_downsampled_1h")
```

## Kubernetes (via Helm)

By default, Flagsmith uses PostgreSQL to store time-series data. You can alternatively use InfluxDB to track:

- SDK API traffic
- SDK Flag Evaluations

You will need to perform the steps above to configure InfluxDB itself. You can then configure the Helm chart with the following values:

| Parameter                                          | Description                                                               | Default                        |
| -------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------ |
| `influxdb2.enabled`                                |                                                                           | `true`                         |
| `influxdb2.nameOverride`                           |                                                                           | `influxdb`                     |
| `influxdb2.image.repository`                       | Docker image repository for InfluxDB                                      | `quay.io/influxdb/influxdb`    |
| `influxdb2.image.tag`                              | Docker image tag for InfluxDB                                             | `v2.0.2`                       |
| `influxdb2.image.imagePullPolicy`                  |                                                                           | `IfNotPresent`                 |
| `influxdb2.image.imagePullSecrets`                 |                                                                           | `[]`                           |
| `influxdb2.adminUser.organization`                 |                                                                           | `influxdata`                   |
| `influxdb2.adminUser.bucket`                       |                                                                           | `default`                      |
| `inflxdb2.adminUser.user`                          |                                                                           | `admin`                        |
| `influxdb2.adminUser.password`                     |                                                                           | randomly generated             |
| `influxdb2.adminUser.token`                        |                                                                           | randomly generated             |
| `influxdb2.persistence.enabled`                    |                                                                           | `false`                        |
| `influxdb.resources`                               | resources per pod for the InfluxDB                                        | `{}`                           |
| `influxdb.nodeSelector`                            |                                                                           | `{}`                           |
| `influxdb.tolerations`                             |                                                                           | `[]`                           |
| `influxdb.affinity`                                |                                                                           | `{}`                           |
| `influxdbExternal.enabled`                         | Use an InfluxDB not managed by this chart                                 | `false`                        |
| `influxdbExternal.url`                             |                                                                           |                                |
| `influxdbExternal.bucket`                          |                                                                           |                                |
| `influxdbExternal.organization`                    |                                                                           |                                |
| `influxdbExternal.token`                           |                                                                           |                                |
| `influxdbExternal.tokenFromExistingSecret.enabled` | Use reference to a k8s secret not managed by this chart                   | `false`                        |
| `influxdbExternal.tokenFromExistingSecret.name`    | Referenced secret name                                                    |                                |
| `influxdbExternal.tokenFromExistingSecret.key`     | Key within the referenced secret to use                                   |                                |

