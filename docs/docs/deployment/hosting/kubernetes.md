---
title: Kubernetes
sidebar_position: 50
---

## Overview

Check out our [Kubernetes Chart Repository on GitHub](https://github.com/Flagsmith/flagsmith-charts) and our
[published Helm Charts](https://flagsmith.github.io/flagsmith-charts/).

## Quick-start

```bash
helm repo add flagsmith https://flagsmith.github.io/flagsmith-charts/
helm install -n flagsmith --create-namespace flagsmith flagsmith/flagsmith
kubectl -n flagsmith port-forward svc/flagsmith-frontend 8080:8080
```

Then view `http://localhost:8080` in a browser. This will install the chart using default options, in a new namespace
`flagsmith`.

Refer to the chart's default
[`values.yaml`](https://github.com/Flagsmith/flagsmith-charts/blob/main/charts/flagsmith/values.yaml) file to learn
which values are expected by the chart. You can use it as a reference for building your own values file:

```bash
wget https://raw.githubusercontent.com/Flagsmith/flagsmith-charts/main/charts/flagsmith/values.yaml
helm install -n flagsmith --create-namespace flagsmith flagsmith/flagsmith -f values.yaml
```

We would suggest only doing this when running the platform locally, and recommend reading the Helm docs for
[installation](https://helm.sh/docs/intro/using_helm/#helm-install-installing-a-package),
[upgrading](https://helm.sh/docs/helm/helm_upgrade/) and
[values](https://helm.sh/docs/chart_template_guide/values_files/) for further information.

## Configuration

### Ingress configuration

The above is a quick way of gaining access to Flagsmith, but in many cases you will need to configure ingress to work
with an ingress controller.

#### Port forwarding

In a terminal, run:

```bash
kubectl -n [flagsmith-namespace] port-forward svc/[flagsmith-release-name]-frontend 8080:8080
```

Then access `http://localhost:8080` in a browser.

#### In a cluster that has an ingress controller, using the frontend proxy

In this configuration, api requests are proxied by the frontend. This is simpler to configure, but introduces some
latency.

Set the following values for flagsmith, with changes as needed to accommodate your ingress controller, and any
associated DNS changes.

Eg in the `charts/flagsmith/values.yaml` file:

```yaml
ingress:
 frontend:
  enabled: true
  hosts:
   - host: flagsmith.[MYDOMAIN]
     paths:
      - /
```

Then, once any out-of-cluster DNS or CDN changes have been applied, access `https://flagsmith.[MYDOMAIN]` in a browser.

#### In a cluster that has an ingress controller, using separate ingresses for frontend and api

Set the following values for flagsmith, with changes as needed to accommodate your ingress controller, and any
associated DNS changes. Also, set the `FLAGSMITH_API_URL` env-var such that the URL is reachable from a browser
accessing the frontend.

Eg in the `charts/flagsmith/values.yaml` file:

```yaml
ingress:
 frontend:
  enabled: true
  hosts:
   - host: flagsmith.[MYDOMAIN]
     paths:
      - /
 api:
  enabled: true
  hosts:
   - host: flagsmith.[MYDOMAIN]
     paths:
      - /api/
      - /health/

frontend:
 extraEnv:
  FLAGSMITH_API_URL: 'https://flagsmith.[MYDOMAIN]/api/v1/'
```

Then, once any out-of-cluster DNS or CDN changes have been applied, access `https://flagsmith.[MYDOMAIN]` in a browser.

#### Minikube ingress

(See [https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/] for more details.)

If using minikube, enable ingress with `minikube addons enable ingress`.

Then set the following values for flagsmith in the `charts/flagsmith/values.yaml` file:

```yaml
ingress:
 frontend:
  enabled: true
  hosts:
   - host: flagsmith.local
     paths:
      - /
```

and apply. This will create two ingress resources.

Run `minikube ip`. Set this ip and `flagsmith.local` in your `/etc/hosts`, eg:

```txt
192.168.99.99 flagsmith.local
```

Then access `http://flagsmith.local` in a browser.

### Provided Database configuration

By default, the chart creates its own PostgreSQL server within the cluster, referencing
[https://github.com/helm/charts/tree/master/stable/postgresql](https://github.com/helm/charts/tree/master/stable/postgresql)
for the service.

:::caution

We recommend running an externally managed database in production, either by deploying your own Postgres instance in
your cluster, or using a service like [AWS RDS](https://aws.amazon.com/rds/postgresql/).

:::

You can provide configuration options to the postgres database by modifying the values, for example the below changes
the max_connections in the `charts/flagsmith/values.yaml` file:

```yaml
postgresql:
 enabled: true

 postgresqlConfiguration:
  max_connections: '200' # override the default max_connections of 100
```

### External Database configuration

To connect the Flagsmith API to an external PostgreSQL server set the values under `databaseExternal`, eg in the
`charts/flagsmith/values.yaml` file:

```yaml
postgresql:
 enabled: false # turn off the chart-managed postgres

databaseExternal:
 enabled: true
 # Can specify the full URL
 url: 'postgres://myuser:mypass@myhost:5432/mydbname'
 # Or can specify each part (url takes precedence if set)
 type: postgres
 host: myhost
 port: 5432
 database: mydbname
 username: myuser
 password: mypass
 # Or can specify a pre-existing k8s secret containing the database URL
 urlFromExistingSecret:
  enabled: true
  name: my-precreated-db-config
  key: DB_URL
```

:::caution

Due to a [bug](https://bugs.python.org/issue33342) in python's urllib module, passwords containing `[`, `]` or `#` chars
must be urlencoded.

e.g.

`postgres://user:pass[word@localhost/flagsmith`

should be provided as:

`postgres://user:pass%5Bword@localhost/flagsmith`

:::

### Environment variables

:::caution

It's important to define a [`secretKey`](https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY)
value in your helm chart when running in Kubernetes. Use a password manager to generate a random hash and set this so
that all the API nodes are running with an identical `DJANGO_SECRET_KEY`.

If you are using our Helm charts and don't provide a `secretKey`, one will be generated for you and shared across the
running pods, but this will change upon redeployment, which you probably don't want to happen.

:::

The chart handles most environment variables required, but see the
[API readme](/deployment/hosting/locally-api#environment-variables) for all available configuration options. These can
be set using `api.extraEnv`, eg in the `charts/flagsmith/values.yaml` file:

```yaml
api:
 extraEnv:
  LOG_LEVEL: DEBUG
```

### Resource allocation

By default, no resource limits or requests are set.

TODO: recommend some defaults

### Replicas

By default, 1 replica of each of the frontend and api is used.

TODO: recommend some defaults.

TODO: consider some autoscaling options.

TODO: create a pod-disruption-budget

### Deployment strategy

For each of the deployments, you can set `deploymentStrategy`. By default this is unset, meaning you get the default
Kubernetes behaviour, but you can set this to an object to adjust this. See
[https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy].

Eg in the `charts/flagsmith/values.yaml` file:

```yaml
api:
 deploymentStrategy:
  type: RollingUpdate
  rollingUpdate:
   maxUnavailable: 1
   maxSurge: '50%'
```

### PgBouncer

By default, Flagsmith connects directly to the database - either in-cluster, or external. Can enable PgBouncer with
`pgbouncer.enabled: true` to have Flagsmith connect to PgBouncer, and PgBouncer connect to the database.

### All-in-one Docker image

The Docker image at [https://hub.docker.com/r/flagsmith/flagsmith/] contains both the API and the frontend. To make use
of this, set the following values:

```yaml
api:
 image:
  repository: flagsmith/flagsmith # or some other repository hosting the combined image
  tag: 2.14 # or some other tag that exists in that repository
 separateApiAndFrontend: false
```

This switches off the Kubernetes deployment for the frontend. However, the ingress and service are retained, but all
requests are handled by the API deployment.

### InfluxDB

By default, Flagsmith uses Postgres to store time series data. You can alternatively use Influx to track:

- SDK API traffic
- SDK Flag Evaluations

[You need to perform some additional steps to configure InfluxDB.](/deployment/overview#time-series-data-via-influxdb).

### Task Processor

The task processor itself is documented [here](/deployment/configuration/task-processor). See the table below for the
values to set to configure the task processor using the helm chart.

## Chart Values

The following table lists the configurable parameters of the chart and their default values.

| Parameter                                          | Description                                                               | Default                        |
| -------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------ |
| `api.image.repository`                             | docker image repository for flagsmith api                                 | `flagsmith/flagsmith-api`      |
| `api.image.tag`                                    | docker image tag for flagsmith api                                        | appVersion                     |
| `api.image.imagePullPolicy`                        |                                                                           | `IfNotPresent`                 |
| `api.image.imagePullSecrets`                       |                                                                           | `[]`                           |
| `api.separateApiAndFrontend`                       | Set to false if using flagsmith/flagsmith image for the api               | `true`                         |
| `api.replicacount`                                 | number of replicas for the flagsmith api, `null` to unset                 | 1                              |
| `api.deploymentStrategy`                           | See "Deployment strategy" above                                           |                                |
| `api.resources`                                    | resources per pod for the flagsmith api                                   | `{}`                           |
| `api.podLabels`                                    | additional labels to apply to pods for the flagsmith api                  | `{}`                           |
| `api.extraEnv`                                     | extra environment variables to set for the flagsmith api                  | `{}`                           |
| `api.secretKey`                                    | See `secretKey` docs above                                                | `null`                         |
| `api.secretKeyFromExistingSecret.enabled`          | Set to true to use a secret key stored in an existing k8s secret          | `false`                        |
| `api.secretKeyFromExistingSecret.name`             | The name of the secret key k8s secret                                     | `null`                         |
| `api.secretKeyFromExistingSecret.key`              | The key of the secret key in the k8s secret                               | `null`                         |
| `api.nodeSelector`                                 |                                                                           | `{}`                           |
| `api.tolerations`                                  |                                                                           | `[]`                           |
| `api.affinity`                                     |                                                                           | `{}`                           |
| `api.podSecurityContext`                           |                                                                           | `{}`                           |
| `api.defaultPodSecurityContext.enabled`            | whether to use the default security context                               | `true`                         |
| `api.livenessProbe.failureThreshold`               |                                                                           | 5                              |
| `api.livenessProbe.initialDelaySeconds`            |                                                                           | 10                             |
| `api.livenessProbe.periodSeconds`                  |                                                                           | 10                             |
| `api.livenessProbe.successThreshold`               |                                                                           | 1                              |
| `api.livenessProbe.timeoutSeconds`                 |                                                                           | 2                              |
| `api.logging.format`                               | Outputted log format, either `json` or `generic`                          | `generic`                      |
| `api.readinessProbe.failureThreshold`              |                                                                           | 10                             |
| `api.readinessProbe.initialDelaySeconds`           |                                                                           | 10                             |
| `api.readinessProbe.periodSeconds`                 |                                                                           | 10                             |
| `api.readinessProbe.successThreshold`              |                                                                           | 1                              |
| `api.readinessProbe.timeoutSeconds`                |                                                                           | 2                              |
| `api.dbWaiter.image.repository`                    |                                                                           | `willwill/wait-for-it`         |
| `api.dbWaiter.image.tag`                           |                                                                           | `latest`                       |
| `api.dbWaiter.image.imagePullPolicy`               |                                                                           | `IfNotPresent`                 |
| `api.dbWaiter.timeoutSeconds`                      | Time before init container will retry                                     | 30                             |
| `frontend.enabled`                                 | Whether the flagsmith frontend is enabled                                 | `true`                         |
| `frontend.image.repository`                        | docker image repository for flagsmith frontend                            | `flagsmith/flagsmith-frontend` |
| `frontend.image.tag`                               | docker image tag for flagsmith frontend                                   | appVersion                     |
| `frontend.image.imagePullPolicy`                   |                                                                           | `IfNotPresent`                 |
| `frontend.image.imagePullSecrets`                  |                                                                           | `[]`                           |
| `frontend.replicacount`                            | number of replicas for the flagsmith frontend, `null` to unset            | 1                              |
| `frontend.deploymentStrategy`                      | See "Deployment strategy" above                                           |                                |
| `frontend.resources`                               | resources per pod for the flagsmith frontend                              | `{}`                           |
| `frontend.apiProxy.enabled`                        | proxy API requests to the API service within the cluster                  | `true`                         |
| `frontend.extraEnv`                                | extra environment variables to set for the flagsmith frontend             | `{}`                           |
| `frontend.nodeSelector`                            |                                                                           | `{}`                           |
| `frontend.tolerations`                             |                                                                           | `[]`                           |
| `frontend.affinity`                                |                                                                           | `{}`                           |
| `api.podSecurityContext`                           |                                                                           | `{}`                           |
| `api.defaultPodSecurityContext.enabled`            | whether to use the default security context                               | `true`                         |
| `frontend.livenessProbe.failureThreshold`          |                                                                           | 20                             |
| `frontend.livenessProbe.initialDelaySeconds`       |                                                                           | 20                             |
| `frontend.livenessProbe.periodSeconds`             |                                                                           | 10                             |
| `frontend.livenessProbe.successThreshold`          |                                                                           | 1                              |
| `frontend.livenessProbe.timeoutSeconds`            |                                                                           | 10                             |
| `frontend.readinessProbe.failureThreshold`         |                                                                           | 20                             |
| `frontend.readinessProbe.initialDelaySeconds`      |                                                                           | 20                             |
| `frontend.readinessProbe.periodSeconds`            |                                                                           | 10                             |
| `frontend.readinessProbe.successThreshold`         |                                                                           | 1                              |
| `frontend.readinessProbe.timeoutSeconds`           |                                                                           | 10                             |
| `taskProcessor.image.repository`                   |                                                                           | (same as for `api.image`)      |
| `taskProcessor.image.tag`                          |                                                                           | (same as for `api.image`)      |
| `taskProcessor.image.imagePullPolicy`              |                                                                           | (same as for `api.image`)      |
| `taskProcessor.image.imagePullSecrets`             |                                                                           | (same as for `api.image`)      |
| `taskProcessor.enabled`                            | Whether to run the task processor                                         | `false`                        |
| `taskProcessor.replicacount`                       |                                                                           | 1                              |
| `taskProcessor.sleepIntervalMs`                    | Passed as `--sleepintervalms` to the task processor                       |                                |
| `taskProcessor.numThreads`                         | Passed as `--numthreads` to the task processor                            |                                |
| `taskProcessor.gracePeriodMs`                      | Passed as `--graceperiodms` to the task processor                         |                                |
| `taskProcessor.queuePopSize`                       | Passed as `--queuepopsize` to the task processor                          |                                |
| `taskProcessor.livenessProbe.failureThreshold`     |                                                                           | 5                              |
| `taskProcessor.livenessProbe.initialDelaySeconds`  |                                                                           | 5                              |
| `taskProcessor.livenessProbe.periodSeconds`        |                                                                           | 10                             |
| `taskProcessor.livenessProbe.successThreshold`     |                                                                           | 1                              |
| `taskProcessor.livenessProbe.timeoutSeconds`       |                                                                           | 2                              |
| `taskProcessor.readinessProbe.failureThreshold`    |                                                                           | 10                             |
| `taskProcessor.readinessProbe.initialDelaySeconds` |                                                                           | 1                              |
| `taskProcessor.readinessProbe.periodSeconds`       |                                                                           | 10                             |
| `taskProcessor.readinessProbe.successThreshold`    |                                                                           | 1                              |
| `taskProcessor.readinessProbe.timeoutSeconds`      |                                                                           | 2                              |
| `taskProcessor.podAnnotations`                     |                                                                           | `{}`                           |
| `taskProcessor.resources`                          |                                                                           | `{}`                           |
| `taskProcessor.podLabels`                          |                                                                           | `{}`                           |
| `taskProcessor.nodeSelector`                       |                                                                           | `{}`                           |
| `taskProcessor.tolerations`                        |                                                                           | `[]`                           |
| `taskProcessor.affinity`                           |                                                                           | `{}`                           |
| `taskProcessor.podSecurityContext`                 |                                                                           | `{}`                           |
| `taskProcessor.defaultPodSecurityContext.enabled`  | whether to use the default security context                               | `true`                         |
| `postgresql.enabled`                               | if `true`, creates in-cluster PostgreSQL database                         | `true`                         |
| `postgresql.serviceAccount.enabled`                | creates a serviceaccount for the postgres pod                             | `true`                         |
| `nameOverride`                                     |                                                                           | `flagsmith-postgres`           |
| `postgresqlDatabase`                               |                                                                           | `flagsmith`                    |
| `postgresqlUsername`                               |                                                                           | `postgres`                     |
| `postgresqlPassword`                               |                                                                           | `flagsmith`                    |
| `databaseExternal.enabled`                         | use an external database. Specify database URL, or all parts.             | `false`                        |
| `databaseExternal.url`                             | See [schema](https://github.com/kennethreitz/dj-database-url#url-schema). |                                |
| `databaseExternal.type`                            | Note: Only postgres supported by default images.                          | `postgres`                     |
| `databaseExternal.port`                            |                                                                           | 5432                           |
| `databaseExternal.database`                        | Name of the database within the server                                    |                                |
| `databaseExternal.username`                        |                                                                           |                                |
| `databaseExternal.password`                        |                                                                           |                                |
| `databaseExternal.urlFromExistingSecret.enabled`   | Reference an existing secret containing the database URL.                 |                                |
| `databaseExternal.urlFromExistingSecret.name`      | Name of referenced secret                                                 |                                |
| `databaseExternal.urlFromExistingSecret.key`       | Key within the referenced secrt to use                                    |                                |
| `influxdb2.enabled`                                |                                                                           | `true`                         |
| `influxdb2.nameOverride`                           |                                                                           | `influxdb`                     |
| `influxdb2.image.repository`                       | docker image repository for influxdb                                      | `quay.io/influxdb/influxdb`    |
| `influxdb2.image.tag`                              | docker image tag for influxdb                                             | `v2.0.2`                       |
| `influxdb2.image.imagePullPolicy`                  |                                                                           | `IfNotPresent`                 |
| `influxdb2.image.imagePullSecrets`                 |                                                                           | `[]`                           |
| `influxdb2.adminUser.organization`                 |                                                                           | `influxdata`                   |
| `influxdb2.adminUser.bucket`                       |                                                                           | `default`                      |
| `influxdb2.adminUser.user`                         |                                                                           | `admin`                        |
| `influxdb2.adminUser.password`                     |                                                                           | randomly generated             |
| `influxdb2.adminUser.token`                        |                                                                           | randomly generated             |
| `influxdb2.persistence.enabled`                    |                                                                           | `false`                        |
| `influxdb.resources`                               | resources per pod for the influxdb                                        | `{}`                           |
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
| `pgbouncer.enabled`                                |                                                                           | `false`                        |
| `pgbouncer.image.repository`                       |                                                                           | `bitnami/pgbouncer`            |
| `pgbouncer.image.tag`                              |                                                                           | `1.16.0`                       |
| `pgbouncer.image.imagePullPolicy`                  |                                                                           | `IfNotPresent`                 |
| `pgbouncer.image.imagePullSecrets`                 |                                                                           | `[]`                           |
| `pgbouncer.replicaCount`                           | number of replicas for pgbouncer, `null` to unset                         | 1                              |
| `pgbouncer.deploymentStrategy`                     | See "Deployment strategy" above                                           |                                |
| `pgbouncer.podAnnotations`                         |                                                                           | `{}`                           |
| `pgbouncer.resources`                              |                                                                           | `{}`                           |
| `pgbouncer.podLabels`                              |                                                                           | `{}`                           |
| `pgbouncer.extraEnv`                               |                                                                           | `{}`                           |
| `pgbouncer.nodeSelector`                           |                                                                           | `{}`                           |
| `pgbouncer.tolerations`                            |                                                                           | `[]`                           |
| `pgbouncer.affinity`                               |                                                                           | `{}`                           |
| `pgbouncer.podSecurityContext`                     |                                                                           | `{}`                           |
| `pgbouncer.securityContext`                        |                                                                           | `{}`                           |
| `pgbouncer.defaultSecurityContext.enabled`         |                                                                           | `true`                         |
| `pgbouncer.defaultSecurityContext`                 |                                                                           | `{}`                           |
| `pgbouncer.livenessProbe.failureThreshold`         |                                                                           | 5                              |
| `pgbouncer.livenessProbe.initialDelaySeconds`      |                                                                           | 5                              |
| `pgbouncer.livenessProbe.periodSeconds`            |                                                                           | 10                             |
| `pgbouncer.livenessProbe.successThreshold`         |                                                                           | 1                              |
| `pgbouncer.livenessProbe.timeoutSeconds`           |                                                                           | 2                              |
| `pgbouncer.readinessProbe.failureThreshold`        |                                                                           | 10                             |
| `pgbouncer.readinessProbe.initialDelaySeconds`     |                                                                           | 1                              |
| `pgbouncer.readinessProbe.periodSeconds`           |                                                                           | 10                             |
| `pgbouncer.readinessProbe.successThreshold`        |                                                                           | 1                              |
| `pgbouncer.readinessProbe.timeoutSeconds`          |                                                                           | 2                              |
| `service.influxdb.externalPort`                    |                                                                           | `8080`                         |
| `service.api.type`                                 |                                                                           | `ClusterIP`                    |
| `service.api.port`                                 |                                                                           | `8000`                         |
| `service.frontend.type`                            |                                                                           | `ClusterIP`                    |
| `service.frontend.port`                            |                                                                           | `8080`                         |
| `ingress.frontend.enabled`                         |                                                                           | `false`                        |
| `ingress.frontend.ingressClassName`                |                                                                           |                                |
| `ingress.frontend.annotations`                     |                                                                           | `{}`                           |
| `ingress.frontend.hosts[].host`                    |                                                                           | `chart-example.local`          |
| `ingress.frontend.hosts[].paths`                   |                                                                           | `[]`                           |
| `ingress.frontend.tls`                             |                                                                           | `[]`                           |
| `ingress.api.enabled`                              |                                                                           | `false`                        |
| `ingress.api.ingressClassName`                     |                                                                           |                                |
| `ingress.api.annotations`                          |                                                                           | `{}`                           |
| `ingress.api.hosts[].host`                         |                                                                           | `chart-example.local`          |
| `ingress.api.hosts[].paths`                        |                                                                           | `[]`                           |
| `ingress.api.tls`                                  |                                                                           | `[]`                           |
| `api.statsd.enabled`                               | Enable statsd metric reporting from gunicorn.                             | `false`                        |
| `api.statsd.host`                                  | Host URL to receive statsd metrics                                        | `null`                         |
| `api.statsd.hostFromNodeIp`                        | Set as true to use the node IP as the statsd host instead                 | `false`                        |
| `api.statsd.port`                                  | Host port to receive statsd metrics                                       | `8125`                         |
| `api.statsd.prefix`                                | Prefix to add to metric ids                                               | `flagsmith.api`                |
| `common.labels`                                    | Labels to add to all resources                                            | `{}`                           |
| `common.annotations`                               | Annotations to add to all resources                                       | `{}`                           |

---

## Key upgrade notes

- [0.20.0](https://artifacthub.io/packages/helm/flagsmith/flagsmith/0.20.0): upgrades the bundled in-cluster Postgres.
  This makes no effort to preserve data in the bundled in-cluster Postgres if it is in use. This also renames the
  bundled in-cluster Postgres to have `dev-postgresql` in the name, to signify that it exists such that the chart can be
  deployed self-contained, but that this Postgres instance is treated as disposable. All Flagsmith installations for
  which the data is not disposable [should use an externally managed database](#provided-database-configuration).

## Development and contributing

### Requirements

helm version > 3.0.2

### To run locally

You can test and run the application locally on OSX using `minikube` like this:

```bash
# Install Docker for Desktop and then:

brew install minikube
minikube start --memory 8192 --cpus 4
helm install flagsmith --debug ./flagsmith
minikube dashboard
```

### Test chart installation

Install Chart without building a package:

```bash
helm install flagsmith --debug ./flagsmith
```

Run template and check kubernetes resouces are made:

```bash
helm template flagsmith flagsmith --debug -f flagsmith/values.yaml
```

### Build chart package

To build chart package run:

```bash
helm package ./flagsmith
```
