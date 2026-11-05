---
title: Kubernetes and OpenShift
description: "Deploying Flagsmith on Kubernetes and OpenShift using our Helm charts."
sidebar_position: 2
---

## Overview

This guide covers deploying Flagsmith on Kubernetes or OpenShift using our Helm charts.

Check out our [Kubernetes Chart Repository on GitHub](https://github.com/Flagsmith/flagsmith-charts) and our [published Helm Charts](https://flagsmith.github.io/flagsmith-charts/).

### OpenShift

:::tip

Support for our OpenShift Operator is only available with an [Enterprise plan](https://flagsmith.com/pricing/).

:::

Flagsmith runs on the OpenShift platform via our Helm charts. The rest of this guide is applicable for both Kubernetes and OpenShift.

---

## Quick Start Deployment

### Basic Installation

This is the simplest way to get Flagsmith running for testing or development.

```bash
helm repo add flagsmith https://flagsmith.github.io/flagsmith-charts/
helm install -n flagsmith --create-namespace flagsmith flagsmith/flagsmith
kubectl -n flagsmith port-forward svc/flagsmith-frontend 8080:8080
```

Then view `http://localhost:8080` in a browser. This will install the chart using default options in a new namespace called `flagsmith`.

### Using Custom Values (Optional)

Refer to the chart's default [`values.yaml`](https://github.com/Flagsmith/flagsmith-charts/blob/main/charts/flagsmith/values.yaml) file to learn which values are expected by the chart. You can use it as a reference for building your own values file:

```bash
wget https://raw.githubusercontent.com/Flagsmith/flagsmith-charts/main/charts/flagsmith/values.yaml
helm install -n flagsmith --create-namespace flagsmith flagsmith/flagsmith -f values.yaml
```

:::note

We would suggest only doing this when running the platform locally, and recommend reading the Helm docs for [installation](https://helm.sh/docs/intro/using_helm/#helm-install-installing-a-package), [upgrading](https://helm.sh/docs/helm/helm_upgrade/) and [values](https://helm.sh/docs/chart_template_guide/values_files/) for further information.

:::

---

The above is a quick way of gaining access to Flagsmith, but in many cases you will need to configure ingress to work with an ingress controller.

### Port forwarding

In a terminal, run:

```bash
kubectl -n [flagsmith-namespace] port-forward svc/[flagsmith-release-name]-frontend 8080:8080
```

Then access `http://localhost:8080` in a browser.

### In a cluster that has an ingress controller, using the frontend proxy

In this configuration, API requests are proxied by the frontend. This is simpler to configure but introduces some latency.

Set the following values for Flagsmith, with changes as needed to accommodate your ingress controller and any associated DNS changes.

For example, in the `charts/flagsmith/values.yaml` file:

```yaml
ingress:
 frontend:
  enabled: true
  hosts:
   - flagsmith.[MYDOMAIN]
```

Then, once any out-of-cluster DNS or CDN changes have been applied, access `https://flagsmith.[MYDOMAIN]` in a browser.

### In a cluster that has an ingress controller, using separate ingresses for frontend and API

Set the following values for Flagsmith, with changes as needed to accommodate your ingress controller and any associated DNS changes. Also, set the `FLAGSMITH_API_URL` environment variable such that the URL is reachable from a browser accessing the frontend.

For example, in the `charts/flagsmith/values.yaml` file:

```yaml
ingress:
 frontend:
  enabled: true
  hosts:
   - flagsmith.[MYDOMAIN]

 api:
  enabled: true
  hosts:
   - host: flagsmith.[MYDOMAIN]
     paths:
      - /api/
      - /health/
      - /admin/
      - /static/admin/

frontend:
 extraEnv:
  FLAGSMITH_API_URL: 'https://flagsmith.[MYDOMAIN]/api/v1/'
```

Then, once any out-of-cluster DNS or CDN changes have been applied, access `https://flagsmith.[MYDOMAIN]` in a browser.

### Minikube ingress

(See [https://kubernetes.io/docs/tasks/access-application-cluster/ingress-minikube/] for more details.)

If using minikube, enable ingress with `minikube addons enable ingress`.

Then set the following values for Flagsmith in the `charts/flagsmith/values.yaml` file:

```yaml
ingress:
 frontend:
  enabled: true
  hosts:
   - flagsmith.local
```

and apply. This will create two ingress resources.

Run `minikube ip`. Set this IP and `flagsmith.local` in your `/etc/hosts`, for example:

```txt
192.168.99.99 flagsmith.local
```

Then access `http://flagsmith.local` in a browser.

### Using Gateway API (alternative to Ingress)

The chart supports [Gateway API](https://gateway-api.sigs.k8s.io/) HTTPRoutes as an alternative to Ingress resources.

#### Prerequisites

Install these independently before enabling HTTPRoutes:

1. **Gateway API CRDs**:

   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/latest/download/standard-install.yaml
   ```

2. **A Gateway controller** (e.g., [Envoy Gateway](https://gateway.envoyproxy.io/), Cilium, Istio)
3. **A GatewayClass and Gateway resource** in your cluster. For example, using Envoy Gateway:

   ```yaml
   apiVersion: gateway.networking.k8s.io/v1
   kind: GatewayClass
   metadata:
     name: eg
   spec:
     controllerName: gateway.envoyproxy.io/gatewayclass-controller
   ---
   apiVersion: gateway.networking.k8s.io/v1
   kind: Gateway
   metadata:
     name: my-gateway
     namespace: gateway-ns
   spec:
     gatewayClassName: eg
     listeners:
       - name: http
         port: 80
         protocol: HTTP
         allowedRoutes:
           namespaces:
             from: All
   ```

#### Configuration

The chart only manages HTTPRoute resources. The frontend defaults to routing `/` to the frontend service. The API and SSE routes have no defaults — you must provide rules explicitly.

A typical configuration with separate frontend and API routes:

```yaml
gateway:
  frontend:
    enabled: true
    parentRefs:
      - name: my-gateway
        namespace: gateway-ns
  api:
    enabled: true
    parentRefs:
      - name: my-gateway
        namespace: gateway-ns
    rules:
      - matches:
          - path:
              type: PathPrefix
              value: /api/
          - path:
              type: PathPrefix
              value: /health/
          - path:
              type: PathPrefix
              value: /admin/
          - path:
              type: PathPrefix
              value: /static/admin/
        backendRefs:
          - name: flagsmith-api
            port: 8000

frontend:
  extraEnv:
    FLAGSMITH_API_URL: 'https://flagsmith.[MYDOMAIN]/api/v1/'
```

See the [`values.yaml`](https://github.com/Flagsmith/flagsmith-charts/blob/main/charts/flagsmith/values.yaml) for all available options.

### Provided Database configuration

By default, the chart creates its own PostgreSQL server within the cluster, referencing [https://github.com/helm/charts/tree/master/stable/postgresql](https://github.com/helm/charts/tree/master/stable/postgresql) for the service.

:::caution

We recommend running an externally managed database in production, either by deploying your own PostgreSQL instance in your cluster or using a service like [AWS RDS](https://aws.amazon.com/rds/postgresql/).

:::

You can provide configuration options to the PostgreSQL database by modifying the values. For example, the below changes the max_connections in the `charts/flagsmith/values.yaml` file:

```yaml
postgresql:
 enabled: true

 postgresqlConfiguration:
  max_connections: '200' # override the default max_connections of 100
```

### External Database configuration

To connect the Flagsmith API to an external PostgreSQL server, set the values under `databaseExternal`. For example, in the `charts/flagsmith/values.yaml` file:

```yaml
postgresql:
 enabled: false # turn off the chart-managed PostgreSQL

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

Due to a [bug](https://bugs.python.org/issue33342) in Python's urllib module, passwords containing `[`, `]` or `#` characters must be URL-encoded.

For example:

`postgres://user:pass[word@localhost/flagsmith`

should be provided as:

`postgres://user:pass%5Bword@localhost/flagsmith`

:::

### Environment variables

:::caution

It's important to define a [`secretKey`](https://docs.djangoproject.com/en/4.2/ref/settings/#std-setting-SECRET_KEY) value in your Helm chart when running in Kubernetes. Use a password manager to generate a random hash and set this so that all the API nodes are running with an identical `DJANGO_SECRET_KEY`.

If you are using our Helm charts and don't provide a `secretKey`, one will be generated for you and shared across the running pods, but this will change upon redeployment, which you probably don't want to happen.

:::

The chart handles most environment variables required, but see the [API environment variables](/deployment-self-hosting/core-configuration/environment-variables#api-environment-variables) for all available configuration options. These can be set using `api.extraEnv`. For example, in the `charts/flagsmith/values.yaml` file:

```yaml
api:
 extraEnv:
  LOG_LEVEL: DEBUG
```

### Resource allocation

By default, no resource limits or requests are set.

Our recommended limits are 1vCPU and 2GB RAM for all of our pods, but this might vary depending on your usage pattern
and hosting environment.

### Replicas

By default, 1 replica of each of the frontend, API, and task processor is used. We recommend tailoring these to your
requirements based on expected load, and your hosting environment. As the API will be the most heavily used service, we
would recommend adding more replicas to your API than the other services. A standard configuration, with some built in
fault tolerance, might look something like:

```yaml
frontend:
  replicacount: 2

api:
  replicacount: 4

taskProcessor:
  replicacount: 2
```

### Deployment strategy

For each of the deployments, you can set `deploymentStrategy`. By default this is unset, meaning you get the default
Kubernetes behaviour, but you can set this to an object to adjust this. See
[https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy].

For example, in the `charts/flagsmith/values.yaml` file:

```yaml
api:
 deploymentStrategy:
  type: RollingUpdate
  rollingUpdate:
   maxUnavailable: 1
   maxSurge: '50%'
```

### PgBouncer

By default, Flagsmith connects directly to the database - either in-cluster or external. You can enable PgBouncer with `pgbouncer.enabled: true` to have Flagsmith connect to PgBouncer, and PgBouncer connect to the database.

If you use `databaseExternal.urlFromExistingSecret` to provide the database URL from a pre-existing Kubernetes secret, you must also provide PgBouncer's credentials via a separate existing secret using `pgbouncer.credentialsFromExistingSecret`. This is because Helm cannot read secret values at template time to parse the database URL into PgBouncer's required components.

```yaml
pgbouncer:
  enabled: true
  credentialsFromExistingSecret:
    enabled: true
    name: my-pgbouncer-credentials  # must contain POSTGRESQL_HOST, POSTGRESQL_DATABASE, POSTGRESQL_USER, POSTGRESQL_PASSWORD

databaseExternal:
  enabled: true
  urlFromExistingSecret:
    enabled: true
    name: my-db-url-secret  # DATABASE_URL pointing through PgBouncer
    key: DATABASE_URL
```

### All-in-one Docker image

The Docker image at [https://hub.docker.com/r/flagsmith/flagsmith/] contains both the API and the frontend. To make use of this, set the following values:

```yaml
api:
 image:
  repository: flagsmith/flagsmith # or some other repository hosting the combined image
  tag: 2.14 # or some other tag that exists in that repository
 separateApiAndFrontend: false
```

This switches off the Kubernetes deployment for the frontend. However, the ingress and service are retained, but all requests are handled by the API deployment.

### InfluxDB

By default, Flagsmith uses PostgreSQL to store time series data. You can alternatively use InfluxDB to track:

- SDK API traffic
- SDK Flag Evaluations

[You need to perform some additional steps to configure InfluxDB.](/deployment-self-hosting/scaling-and-performance/using-influxdb-for-analytics).

### Task Processor

The task processor itself is documented [here](/deployment-self-hosting/scaling-and-performance/asynchronous-task-processor). See the table below for the values to set to configure the task processor using the Helm chart.

### Experimentation

The chart can run [experimentation](/experimentation). You bring your own Kafka and data warehouse, and each
environment's events are delivered to the warehouse connected to it. The chart then:

- Runs the event ingestion service, which receives SDK events and writes them to a Kafka topic.
- Runs warehouse delivery, which reads that topic and inserts each environment's events into its warehouse.
- Runs a job after each install and upgrade. The job creates the events topic and a retry topic for failed deliveries.

#### Prerequisites

- Flagsmith API 2.285.0 or later.
- Kafka with at least 3 brokers, for the default replication factor of 3, and a login for Flagsmith with the
  [permissions below](#kafka-topics-and-permissions).
- A data warehouse that you host and run yourself, either ClickHouse or Databricks, reachable from both warehouse
  delivery and the API.

Experiment events are stored in the warehouse rather than in the Flagsmith database, and results are computed by
querying it, so it is infrastructure you provision before enabling experimentation: the managed Flagsmith warehouse is
available only on Flagsmith Cloud. Each environment that runs experiments needs a warehouse connection, created in the
dashboard, but one warehouse can serve every environment, as events are scoped by environment. See
[Connect a warehouse](/experimentation/connect-a-warehouse).

#### Configuration

Add the following to your values file. It turns the experimentation services on, points them at your Kafka, and
publishes the ingestion service so that your applications can reach it:

```yaml
experimentation:
 # Runs the ingestion service, warehouse delivery, and the topic creation job
 enabled: true
 # Optional: provide your own, or the chart generates one
 warehouseCredentialsSecretFromExistingSecret:
  enabled: true
  name: flagsmith-warehouse-credentials
  key: warehouse-credentials-secret
 kafka:
  bootstrapServers: kafka-1:9096,kafka-2:9096,kafka-3:9096
  auth: scram
  username: flagsmith
  password: <password> # Use passwordFromExistingSecret in production

# The ingestion service is the endpoint your SDKs send events to, so it has to be
# reachable from wherever your applications run
ingress:
 ingestion:
  enabled: true
  hosts:
   - host: events.flagsmith.example.com
     paths:
      - /
```

#### Kafka topics and permissions

The chart creates two topics, `flagsmith_warehouse_events` and `flagsmith_warehouse_events_retry`. Use
`experimentation.kafka.topic` and `experimentation.kafka.retryTopic` respectively to optionally change their names.

The Kafka login needs these permissions:

- Read and write both topics.
- Read the consumer groups `warehouse-delivery` and `warehouse-delivery-retry`, which warehouse delivery consumes with.

To keep topic creation away from the runtime login, give the topic creation job its own admin login with
`jobs.experimentationInit.kafka`.

If your brokers have `auto.create.topics.enable=true`, create both topics yourself before enabling experimentation. The
services connect before that job runs, so the brokers would otherwise create them with their default partition count.

#### Database users

The ingestion service and warehouse delivery both connect to the Flagsmith database as the API's user by default. To
limit what each one can reach, create a user of its own and grant it only what it needs.

The ingestion service checks the SDK key on every event it receives, so it only needs to read the environment keys view:

```sql
CREATE ROLE ingestion_server WITH LOGIN PASSWORD '<password>';
GRANT CONNECT ON DATABASE flagsmith TO ingestion_server;
GRANT USAGE ON SCHEMA public TO ingestion_server;
GRANT SELECT ON experimentation_environment_keys TO ingestion_server;
```

Warehouse delivery reads each environment's warehouse connection, and records the delivery status that the dashboard
shows:

```sql
CREATE ROLE warehouse_delivery WITH LOGIN PASSWORD '<password>';
GRANT CONNECT ON DATABASE flagsmith TO warehouse_delivery;
GRANT USAGE ON SCHEMA public TO warehouse_delivery;
GRANT SELECT ON experimentation_delivery_connections TO warehouse_delivery;
GRANT SELECT, INSERT, UPDATE ON experimentation_warehousedeliverystatus TO warehouse_delivery;
```

Store each user's connection URL in a Kubernetes secret, then point the service at it with
`experimentation.ingestion.databaseUrlFromExistingSecret` or
`experimentation.warehouseDelivery.databaseUrlFromExistingSecret`.

## Chart Values

The following table lists the configurable parameters of the chart and their default values.

| Parameter                                          | Description                                                               | Default                        |
| -------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------ |
| `api.image.repository`                             | Docker image repository for Flagsmith API                                 | `flagsmith/flagsmith-api`      |
| `api.image.tag`                                    | Docker image tag for Flagsmith API                                        | appVersion                     |
| `api.image.imagePullPolicy`                        |                                                                           | `IfNotPresent`                 |
| `api.image.imagePullSecrets`                       |                                                                           | `[]`                           |
| `api.separateApiAndFrontend`                       | Set to false if using flagsmith/flagsmith image for the API               | `true`                         |
| `api.replicacount`                                 | Number of replicas for the Flagsmith API, `null` to unset                 | 1                              |
| `api.deploymentStrategy`                           | See "Deployment strategy" above                                           |                                |
| `api.resources`                                    | Resources per pod for the Flagsmith API                                   | `{}`                           |
| `api.podLabels`                                    | Additional labels to apply to pods for the Flagsmith API                  | `{}`                           |
| `api.extraEnv`                                     | Extra environment variables to set for the Flagsmith API                  | `{}`                           |
| `api.secretKey`                                    | See `secretKey` docs above                                                | `null`                         |
| `api.secretKeyFromExistingSecret.enabled`          | Set to true to use a secret key stored in an existing k8s secret          | `false`                        |
| `api.secretKeyFromExistingSecret.name`             | The name of the secret key k8s secret                                     | `null`                         |
| `api.secretKeyFromExistingSecret.key`              | The key of the secret key in the k8s secret                               | `null`                         |
| `api.nodeSelector`                                 |                                                                           | `{}`                           |
| `api.tolerations`                                  |                                                                           | `[]`                           |
| `api.affinity`                                     |                                                                           | `{}`                           |
| `api.podSecurityContext`                           |                                                                           | `{}`                           |
| `api.defaultPodSecurityContext.enabled`            | Whether to use the default security context                               | `true`                         |
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
| `frontend.enabled`                                 | Whether the Flagsmith frontend is enabled                                 | `true`                         |
| `frontend.image.repository`                        | Docker image repository for Flagsmith frontend                            | `flagsmith/flagsmith-frontend` |
| `frontend.image.tag`                               | Docker image tag for Flagsmith frontend                                   | appVersion                     |
| `frontend.image.imagePullPolicy`                   |                                                                           | `IfNotPresent`                 |
| `frontend.image.imagePullSecrets`                  |                                                                           | `[]`                           |
| `frontend.replicacount`                            | Number of replicas for the Flagsmith frontend, `null` to unset            | 1                              |
| `frontend.deploymentStrategy`                      | See "Deployment strategy" above                                           |                                |
| `frontend.resources`                               | Resources per pod for the Flagsmith frontend                              | `{}`                           |
| `frontend.apiProxy.enabled`                        | Proxy API requests to the API service within the cluster                  | `true`                         |
| `frontend.extraEnv`                                | Extra environment variables to set for the Flagsmith frontend             | `{}`                           |
| `frontend.nodeSelector`                            |                                                                           | `{}`                           |
| `frontend.tolerations`                             |                                                                           | `[]`                           |
| `frontend.affinity`                                |                                                                           | `{}`                           |
| `api.podSecurityContext`                           |                                                                           | `{}`                           |
| `api.defaultPodSecurityContext.enabled`            | Whether to use the default security context                               | `true`                         |
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
| `taskProcessor.defaultPodSecurityContext.enabled`  | Whether to use the default security context                               | `true`                         |
| `devPostgresql.enabled`                            | If `true`, creates in-cluster PostgreSQL database                         | `true`                         |
| `postgresql.serviceAccount.enabled`                | Creates a service account for the PostgreSQL pod                          | `true`                         |
| `nameOverride`                                     |                                                                           | `flagsmith-postgres`           |
| `postgresqlDatabase`                               |                                                                           | `flagsmith`                    |
| `postgresqlUsername`                               |                                                                           | `postgres`                     |
| `postgresqlPassword`                               |                                                                           | `flagsmith`                    |
| `databaseExternal.enabled`                         | Use an external database. Specify database URL, or all parts.             | `false`                        |
| `databaseExternal.url`                             | See [schema](https://github.com/kennethreitz/dj-database-url#url-schema). |                                |
| `databaseExternal.type`                            | Note: Only PostgreSQL supported by default images.                        | `postgres`                     |
| `databaseExternal.port`                            |                                                                           | 5432                           |
| `databaseExternal.database`                        | Name of the database within the server                                    |                                |
| `databaseExternal.username`                        |                                                                           |                                |
| `databaseExternal.password`                        |                                                                           |                                |
| `databaseExternal.urlFromExistingSecret.enabled`   | Reference an existing secret containing the database URL.                 |                                |
| `databaseExternal.urlFromExistingSecret.name`      | Name of referenced secret                                                 |                                |
| `databaseExternal.urlFromExistingSecret.key`       | Key within the referenced secret to use                                   |                                |
| `influxdb2.enabled`                                |                                                                           | `true`                         |
| `influxdb2.nameOverride`                           |                                                                           | `influxdb`                     |
| `influxdb2.image.repository`                       | Docker image repository for InfluxDB                                      | `quay.io/influxdb/influxdb`    |
| `influxdb2.image.tag`                              | Docker image tag for InfluxDB                                             | `v2.0.2`                       |
| `influxdb2.image.imagePullPolicy`                  |                                                                           | `IfNotPresent`                 |
| `influxdb2.image.imagePullSecrets`                 |                                                                           | `[]`                           |
| `influxdb2.adminUser.organization`                 |                                                                           | `influxdata`                   |
| `influxdb2.adminUser.bucket`                       |                                                                           | `default`                      |
| `influxdb2.adminUser.user`                         |                                                                           | `admin`                        |
| `influxdb2.adminUser.password`                     |                                                                           | randomly generated             |
| `influxdb2.adminUser.token`                        |                                                                           | randomly generated             |
| `influxdb2.persistence.enabled`                    |                                                                           | `false`                        |
| `influxdb.resources`                               | Resources per pod for the InfluxDB                                        | `{}`                           |
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
| `pgbouncer.credentialsFromExistingSecret.enabled`  | Use an existing secret for PgBouncer credentials instead of generating one. The secret must contain keys: `POSTGRESQL_HOST`, `POSTGRESQL_DATABASE`, `POSTGRESQL_USER`, `POSTGRESQL_PASSWORD`. | `false` |
| `pgbouncer.credentialsFromExistingSecret.name`     | Name of the existing secret containing PgBouncer credentials.             |                                |
| `pgbouncer.enabled`                                |                                                                           | `false`                        |
| `pgbouncer.image.repository`                       |                                                                           | `bitnami/pgbouncer`            |
| `pgbouncer.image.tag`                              |                                                                           | `1.16.0`                       |
| `pgbouncer.image.imagePullPolicy`                  |                                                                           | `IfNotPresent`                 |
| `pgbouncer.image.imagePullSecrets`                 |                                                                           | `[]`                           |
| `pgbouncer.replicaCount`                           | Number of replicas for PgBouncer, `null` to unset                         | 1                              |
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
| `ingress.frontend.hosts`                           | List of hostnames for frontend ingress                                    | `[chart-example.local]`        |
| `ingress.frontend.tls`                             |                                                                           | `[]`                           |
| `ingress.api.enabled`                              |                                                                           | `false`                        |
| `ingress.api.ingressClassName`                     |                                                                           |                                |
| `ingress.api.annotations`                          |                                                                           | `{}`                           |
| `ingress.api.hosts[].host`                         |                                                                           | `chart-example.local`          |
| `ingress.api.hosts[].paths`                        |                                                                           | `[]`                           |
| `ingress.api.tls`                                  |                                                                           | `[]`                           |
| `ingress.ingestion.enabled`                        | Expose event ingestion with an Ingress                                    | `false`                        |
| `ingress.ingestion.hosts`                          | Hosts for that Ingress                                                    | `[]`                           |
| `api.statsd.enabled`                               | Enable statsd metric reporting from gunicorn.                             | `false`                        |
| `api.statsd.host`                                  | Host URL to receive statsd metrics                                        | `null`                         |
| `api.statsd.hostFromNodeIp`                        | Set as true to use the node IP as the statsd host instead                 | `false`                        |
| `api.statsd.port`                                  | Host port to receive statsd metrics                                       | `8125`                         |
| `api.statsd.prefix`                                | Prefix to add to metric IDs                                               | `flagsmith.api`                |
| `common.labels`                                    | Labels to add to all resources                                            | `{}`                           |
| `common.annotations`                               | Annotations to add to all resources                                       | `{}`                           |
| `experimentation.enabled`                          | Run event ingestion and warehouse delivery, and turn experimentation on in the API | `false`                        |
| `experimentation.kafka.bootstrapServers`           | Kafka brokers, e.g. `host1:9096,host2:9096`                               | `null`                         |
| `experimentation.kafka.topic`                      | Topic for experiment events                                               | `flagsmith_warehouse_events`   |
| `experimentation.kafka.retryTopic`                 | Topic for events warehouse delivery retries                               | `flagsmith_warehouse_events_retry` |
| `experimentation.kafka.topicPartitions`            | Partitions for both topics                                                | `8`                            |
| `experimentation.kafka.topicReplicationFactor`     | Replication factor for both topics                                        | `3`                            |
| `experimentation.kafka.auth`                       | `scram` (SASL/SCRAM-SHA-512 over TLS) or `none`                           | `scram`                        |
| `experimentation.kafka.username`                   | Kafka username for `scram`                                                | `null`                         |
| `experimentation.kafka.password`                   | Kafka password for `scram`                                                | `null`                         |
| `experimentation.kafka.passwordFromExistingSecret.enabled` | Read the Kafka password from an existing k8s secret                       | `false`                        |
| `experimentation.kafka.passwordFromExistingSecret.name` | Name of that secret                                                       | `null`                         |
| `experimentation.kafka.passwordFromExistingSecret.key` | Key of the password in that secret                                        | `null`                         |
| `experimentation.warehouseCredentialsSecretFromExistingSecret.enabled` | Read the warehouse credentials secret from an existing k8s secret, instead of generating it | `false`                        |
| `experimentation.warehouseCredentialsSecretFromExistingSecret.name` | Name of that secret                                                       | `""`                           |
| `experimentation.warehouseCredentialsSecretFromExistingSecret.key` | Key of the value in that secret                                           | `warehouse-credentials-secret` |
| `experimentation.ingestion.image.repository`       | Docker image repository for event ingestion                               | `flagsmith/events-ingestion-api` |
| `experimentation.ingestion.image.tag`              | Docker image tag for event ingestion                                      | `0.5`                          |
| `experimentation.ingestion.resources`              | Resources for event ingestion                                             | see `values.yaml`              |
| `experimentation.ingestion.databaseUrlFromExistingSecret.enabled` | Connect event ingestion with its own database user, from an existing k8s secret | `false`                        |
| `experimentation.ingestion.databaseUrlFromExistingSecret.name` | Name of that secret                                                       | `null`                         |
| `experimentation.ingestion.databaseUrlFromExistingSecret.key` | Key of the database URL in that secret                                    | `null`                         |
| `experimentation.warehouseDelivery.image.repository` | Docker image repository for warehouse delivery                            | `flagsmith/warehouse-delivery` |
| `experimentation.warehouseDelivery.image.tag`      | Docker image tag for warehouse delivery                                   | `0.4.0`                        |
| `experimentation.warehouseDelivery.replicaCount`   | Replicas for warehouse delivery; more than `topicPartitions` sit idle     | `1`                            |
| `experimentation.warehouseDelivery.resources`      | Resources for warehouse delivery                                          | see `values.yaml`              |
| `experimentation.warehouseDelivery.databaseUrlFromExistingSecret.enabled` | Connect warehouse delivery with its own database user, from an existing k8s secret | `false`                        |
| `experimentation.warehouseDelivery.databaseUrlFromExistingSecret.name` | Name of that secret                                                       | `null`                         |
| `experimentation.warehouseDelivery.databaseUrlFromExistingSecret.key` | Key of the database URL in that secret                                    | `null`                         |
| `experimentation.warehouseDelivery.extraEnv`       | Extra environment variables for warehouse delivery, e.g. `BATCH_MAX_RECORDS` | `{}`                           |
| `jobs.experimentationInit.kafkaImage`              | Image for the job that creates the Kafka topics                           | `apache/kafka:4.3.1`           |
| `jobs.experimentationInit.kafka.username`          | Admin Kafka username for creating the topics; defaults to `experimentation.kafka.username` | `null`                         |
| `jobs.experimentationInit.kafka.passwordFromExistingSecret.enabled` | Read that admin password from an existing k8s secret                      | `false`                        |
| `jobs.experimentationInit.kafka.passwordFromExistingSecret.name` | Name of that secret                                                       | `null`                         |
| `jobs.experimentationInit.kafka.passwordFromExistingSecret.key` | Key of the password in that secret                                        | `null`                         |

---

## Key Upgrade Notes

- [0.37.0](https://artifacthub.io/packages/helm/flagsmith/flagsmith/0.37.0): upgrades the bundled in-cluster PostgreSQL. This makes no effort to preserve data in the bundled in-cluster PostgreSQL if it is in use. This also renames the bundled in-cluster PostgreSQL to have `dev-postgresql` in the name, to signify that it exists such that the chart can be deployed self-contained, but that this PostgreSQL instance is treated as disposable. All Flagsmith installations for which the data is not disposable [should use an externally managed database](#provided-database-configuration).

---

## Development and Contributing

### Requirements

Helm version > 3.0.2

### Running Locally

You can test and run the application locally on macOS using `minikube` like this:

```bash
# Install Docker for Desktop and then:

brew install minikube
minikube start --memory 8192 --cpus 4
helm install flagsmith --debug ./flagsmith
minikube dashboard
```

### Test Chart Installation

Install Chart without building a package:

```bash
helm install flagsmith --debug ./flagsmith
```

Run template and check Kubernetes resources are made:

```bash
helm template flagsmith flagsmith --debug -f flagsmith/values.yaml
```

### Build Chart Package

To build chart package run:

```bash
helm package ./flagsmith
```
