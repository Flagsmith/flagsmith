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

Then view `http://localhost:8080` in a browser. This will install using default options, in a new namespace `flagsmith`.

### Ingress configuration

The above is a quick and simple way of gaining access to Flagsmith, but in many cases will need to configure ingress to
work with an ingress controller.

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

Eg:

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
associated DNS changes. Also, set the `API_URL` env-var such that the URL is reachable from a browser accessing the
frontend.

Eg:

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
  API_URL: 'https://flagsmith.[MYDOMAIN]/api/v1/'
```

Then, once any out-of-cluster DNS or CDN changes have been applied, access `https://flagsmith.[MYDOMAIN]` in a browser.

#### Minikube ingress

(See https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/ for more details.)

If using minikube, enable ingress with `minikube addons enable ingress`.

Then set the following values for flagsmith:

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

### Database configuration

By default, the chart creates its own PostgreSQL server within the cluster.

To connect the Flagsmith API to an external PostgreSQL server set the values under `databaseExternal`, eg:

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

### Environment variables

The chart handles most environment variables required, but see the
[API readme](https://github.com/Flagsmith/flagsmith-api/blob/main/readme.md#environment-variables) for all available
configuration options. These can be set using `api.extraEnv`, eg:

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

### InfluxDB

By default, Flagsmith uses InfluxDB to store time series data. Currently this is used to measure:

- SDK API traffic
- SDK Flag Evaluations

[Setting up InfluxDB is discussed in more detail in the Docs](/deployment/overview#influxdb).

### PgBouncer

By default, Flagsmith connects directly to the database - either in-cluster, or external. Can enable PgBouncer with
`pgbouncer.enabled: true` to have Flagsmith connect to PgBouncer, and PgBouncer connect to the database.

### All-in-one Docker image

The Docker image at https://hub.docker.com/r/flagsmith/flagsmith/ contains both the API and the frontend. To make use of
this, set the following values:

```yaml
api:
 image:
  repository: flagsmith/flagsmith # or some other repository hosting the combined image
  tag: 2.14 # or some other tag that exists in that repository
 separateApiAndFrontend: false
```

This switches off the Kubernetes deployment for the frontend. However, the ingress and service are retained, but all
requests are handled by the API deployment.

## Configuration

The following table lists the configurable parameters of the chart and their default values.

| Parameter                                          | Description                                                    | Default                        |
| -------------------------------------------------- | -------------------------------------------------------------- | ------------------------------ |
| `api.image.repository`                             | docker image repository for flagsmith api                      | `flagsmith/flagsmith-api`      |
| `api.image.tag`                                    | docker image tag for flagsmith api                             | appVersion                     |
| `api.image.imagePullPolicy`                        |                                                                | `IfNotPresent`                 |
| `api.image.imagePullSecrets`                       |                                                                | `[]`                           |
| `api.separateApiAndFrontend`                       | Set to false if using flagsmith/flagsmith image for the api    | `true`                         |
| `api.replicacount`                                 | number of replicas for the flagsmith api                       | 1                              |
| `api.resources`                                    | resources per pod for the flagsmith api                        | `{}`                           |
| `api.podLabels`                                    | additional labels to apply to pods for the flagsmith api       | `{}`                           |
| `api.extraEnv`                                     | extra environment variables to set for the flagsmith api       | `{}`                           |
| `api.nodeSelector`                                 |                                                                | `{}`                           |
| `api.tolerations`                                  |                                                                | `[]`                           |
| `api.affinity`                                     |                                                                | `{}`                           |
| `api.podSecurityContext`                           |                                                                | `{}`                           |
| `api.defaultPodSecurityContext.enabled`            | whether to use the default security context                    | `true`                         |
| `api.livenessProbe.failureThreshold`               |                                                                | 5                              |
| `api.livenessProbe.initialDelaySeconds`            |                                                                | 10                             |
| `api.livenessProbe.periodSeconds`                  |                                                                | 10                             |
| `api.livenessProbe.successThreshold`               |                                                                | 1                              |
| `api.livenessProbe.timeoutSeconds`                 |                                                                | 2                              |
| `api.readinessProbe.failureThreshold`              |                                                                | 10                             |
| `api.readinessProbe.initialDelaySeconds`           |                                                                | 10                             |
| `api.readinessProbe.periodSeconds`                 |                                                                | 10                             |
| `api.readinessProbe.successThreshold`              |                                                                | 1                              |
| `api.readinessProbe.timeoutSeconds`                |                                                                | 2                              |
| `api.dbWaiter.image.repository`                    |                                                                | `willwill/wait-for-it`         |
| `api.dbWaiter.image.tag`                           |                                                                | `latest`                       |
| `api.dbWaiter.image.imagePullPolicy`               |                                                                | `IfNotPresent`                 |
| `api.dbWaiter.timeoutSeconds`                      | Time before init container will retry                          | 30                             |
| `frontend.enabled`                                 | Whether the flagsmith frontend is enabled                      | `true`                         |
| `frontend.image.repository`                        | docker image repository for flagsmith frontend                 | `flagsmith/flagsmith-frontend` |
| `frontend.image.tag`                               | docker image tag for flagsmith frontend                        | appVersion                     |
| `frontend.image.imagePullPolicy`                   |                                                                | `IfNotPresent`                 |
| `frontend.image.imagePullSecrets`                  |                                                                | `[]`                           |
| `frontend.replicacount`                            | number of replicas for the flagsmith frontend                  | 1                              |
| `frontend.resources`                               | resources per pod for the flagsmith frontend                   | `{}`                           |
| `frontend.apiProxy.enabled`                        | proxy API requests to the API service within the cluster       | `true`                         |
| `frontend.extraEnv`                                | extra environment variables to set for the flagsmith frontend  | `{}`                           |
| `frontend.nodeSelector`                            |                                                                | `{}`                           |
| `frontend.tolerations`                             |                                                                | `[]`                           |
| `frontend.affinity`                                |                                                                | `{}`                           |
| `api.podSecurityContext`                           |                                                                | `{}`                           |
| `api.defaultPodSecurityContext.enabled`            | whether to use the default security context                    | `true`                         |
| `frontend.livenessProbe.failureThreshold`          |                                                                | 20                             |
| `frontend.livenessProbe.initialDelaySeconds`       |                                                                | 20                             |
| `frontend.livenessProbe.periodSeconds`             |                                                                | 10                             |
| `frontend.livenessProbe.successThreshold`          |                                                                | 1                              |
| `frontend.livenessProbe.timeoutSeconds`            |                                                                | 10                             |
| `frontend.readinessProbe.failureThreshold`         |                                                                | 20                             |
| `frontend.readinessProbe.initialDelaySeconds`      |                                                                | 20                             |
| `frontend.readinessProbe.periodSeconds`            |                                                                | 10                             |
| `frontend.readinessProbe.successThreshold`         |                                                                | 1                              |
| `frontend.readinessProbe.timeoutSeconds`           |                                                                | 10                             |
| `postgresql.enabled`                               | if `true`, creates in-cluster PostgreSQL database              | `true`                         |
| `postgresql.serviceAccount.enabled`                | creates a serviceaccount for the postgres pod                  | `true`                         |
| `nameOverride`                                     |                                                                | `flagsmith-postgres`           |
| `postgresqlDatabase`                               |                                                                | `flagsmith`                    |
| `postgresqlUsername`                               |                                                                | `postgres`                     |
| `postgresqlPassword`                               |                                                                | `flagsmith`                    |
| `databaseExternal.enabled`                         | use an external database. Specify database URL, or all parts.  | `false`                        |
| `databaseExternal.url`                             | See https://github.com/kennethreitz/dj-database-url#url-schema |                                |
| `databaseExternal.type`                            | Note: Only postgres supported by default images.               | `postgres`                     |
| `databaseExternal.port`                            |                                                                | 5432                           |
| `databaseExternal.database`                        | Name of the database within the server                         |                                |
| `databaseExternal.username`                        |                                                                |                                |
| `databaseExternal.password`                        |                                                                |                                |
| `databaseExternal.urlFromExistingSecret.enabled`   | Reference an existing secret containing the database URL       |                                |
| `databaseExternal.urlFromExistingSecret.name`      | Name of referenced secret                                      |                                |
| `databaseExternal.urlFromExistingSecret.key`       | Key within the referenced secrt to use                         |                                |
| `influxdb.enabled`                                 |                                                                | `true`                         |
| `influxdb.nameOverride`                            |                                                                | `influxdb`                     |
| `influxdb.image.repository`                        | docker image repository for influxdb                           | `quay.io/influxdb/influxdb`    |
| `influxdb.image.tag`                               | docker image tag for influxdb                                  | `v2.0.2`                       |
| `influxdb.image.imagePullPolicy`                   |                                                                | `IfNotPresent`                 |
| `influxdb.image.imagePullSecrets`                  |                                                                | `[]`                           |
| `influxdb.adminUser.organization`                  |                                                                | `influxdata`                   |
| `influxdb.adminUser.bucket`                        |                                                                | `default`                      |
| `influxdb.adminUser.user`                          |                                                                | `admin`                        |
| `influxdb.adminUser.password`                      |                                                                | randomly generated             |
| `influxdb.adminUser.token`                         |                                                                | randomly generated             |
| `influxdb.persistence.enabled`                     |                                                                | `false`                        |
| `influxdb.resources`                               | resources per pod for the influxdb                             | `{}`                           |
| `influxdb.nodeSelector`                            |                                                                | `{}`                           |
| `influxdb.tolerations`                             |                                                                | `[]`                           |
| `influxdb.affinity`                                |                                                                | `{}`                           |
| `influxdbExternal.enabled`                         | Use an InfluxDB not managed by this chart                      | `false`                        |
| `influxdbExternal.url`                             |                                                                |                                |
| `influxdbExternal.bucket`                          |                                                                |                                |
| `influxdbExternal.organization`                    |                                                                |                                |
| `influxdbExternal.token`                           |                                                                |                                |
| `influxdbExternal.tokenFromExistingSecret.enabled` | Use reference to a k8s secret not managed by this chart        | `false`                        |
| `influxdbExternal.tokenFromExistingSecret.name`    | Referenced secret name                                         |                                |
| `influxdbExternal.tokenFromExistingSecret.key`     | Key within the referenced secret to use                        |                                |
| `pgbouncer.enabled`                                |                                                                | `false`                        |
| `pgbouncer.image.repository`                       |                                                                | `bitnami/pgbouncer`            |
| `pgbouncer.image.tag`                              |                                                                | `1.16.0`                       |
| `pgbouncer.image.imagePullPolicy`                  |                                                                | `IfNotPresent`                 |
| `pgbouncer.image.imagePullSecrets`                 |                                                                | `[]`                           |
| `pgbouncer.replicaCount`                           |                                                                | 1                              |
| `pgbouncer.podAnnotations`                         |                                                                | `{}`                           |
| `pgbouncer.resources`                              |                                                                | `{}`                           |
| `pgbouncer.podLabels`                              |                                                                | `{}`                           |
| `pgbouncer.extraEnv`                               |                                                                | `{}`                           |
| `pgbouncer.nodeSelector`                           |                                                                | `{}`                           |
| `pgbouncer.tolerations`                            |                                                                | `[]`                           |
| `pgbouncer.affinity`                               |                                                                | `{}`                           |
| `pgbouncer.podSecurityContext`                     |                                                                | `{}`                           |
| `pgbouncer.securityContext`                        |                                                                | `{}`                           |
| `pgbouncer.defaultSecurityContext.enabled`         |                                                                | `true`                         |
| `pgbouncer.defaultSecurityContext`                 |                                                                | `{}`                           |
| `pgbouncer.livenessProbe.failureThreshold`         |                                                                | 5                              |
| `pgbouncer.livenessProbe.initialDelaySeconds`      |                                                                | 5                              |
| `pgbouncer.livenessProbe.periodSeconds`            |                                                                | 10                             |
| `pgbouncer.livenessProbe.successThreshold`         |                                                                | 1                              |
| `pgbouncer.livenessProbe.timeoutSeconds`           |                                                                | 2                              |
| `pgbouncer.readinessProbe.failureThreshold`        |                                                                | 10                             |
| `pgbouncer.readinessProbe.initialDelaySeconds`     |                                                                | 1                              |
| `pgbouncer.readinessProbe.periodSeconds`           |                                                                | 10                             |
| `pgbouncer.readinessProbe.successThreshold`        |                                                                | 1                              |
| `pgbouncer.readinessProbe.timeoutSeconds`          |                                                                | 2                              |
| `service.influxdb.externalPort`                    |                                                                | `8080`                         |
| `service.api.type`                                 |                                                                | `ClusterIP`                    |
| `service.api.port`                                 |                                                                | `8000`                         |
| `service.frontend.type`                            |                                                                | `ClusterIP`                    |
| `service.frontend.port`                            |                                                                | `8080`                         |
| `ingress.frontend.enabled`                         |                                                                | `false`                        |
| `ingress.frontend.ingressClassName`                |                                                                |                                |
| `ingress.frontend.annotations`                     |                                                                | `{}`                           |
| `ingress.frontend.hosts[].host`                    |                                                                | `chart-example.local`          |
| `ingress.frontend.hosts[].paths`                   |                                                                | `[]`                           |
| `ingress.frontend.tls`                             |                                                                | `[]`                           |
| `ingress.api.enabled`                              |                                                                | `false`                        |
| `ingress.api.ingressClassName`                     |                                                                |                                |
| `ingress.api.annotations`                          |                                                                | `{}`                           |
| `ingress.api.hosts[].host`                         |                                                                | `chart-example.local`          |
| `ingress.api.hosts[].paths`                        |                                                                | `[]`                           |
| `ingress.api.tls`                                  |                                                                | `[]`                           |

---

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

### Test install Chart

Install Chart without building a package:

```bash
helm install flagsmith --debug ./flagsmith
```

Run template and check kubernetes resouces are made:

```bash
helm template flagsmith flagsmith --debug -f flagsmith/values.yaml
```

### build chart package

To build chart package run:

```bash
helm package ./flagsmith
```
