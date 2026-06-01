---
title: Deploying Flagsmith on Google Cloud
sidebar_label: Google Cloud
sidebar_position: 20
---

## Overview

Flagsmith can be deployed on Google Cloud Platform using either of two approaches:

- **[Google Kubernetes Engine (GKE)](#gke-recommended-for-production)** with our Helm charts — recommended for
  production and enterprise deployments.
- **[Cloud Run](#cloud-run-quick-start)** — a simpler option for evaluation or smaller workloads.

:::tip

For production and enterprise deployments, we recommend GKE with our
[Helm charts](https://github.com/Flagsmith/flagsmith-charts). This gives you full control over scaling, networking, and
operational tooling.

:::

---

## GKE (Recommended for Production)

### Cluster Setup

We recommend [GKE Standard](https://cloud.google.com/kubernetes-engine/docs/concepts/choose-cluster-mode) or
[GKE Autopilot](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview) depending on how much
control you need over node configuration. Either mode works well with Flagsmith.

For node pool sizing guidance, see our
[sizing and scaling page](/deployment-self-hosting/scaling-and-performance/sizing-and-scaling). As a starting point, our
recommended resource allocation per pod is 1 vCPU and 2 GB RAM.

### Deploying Flagsmith with Helm

We publish official Helm charts for deploying Flagsmith on Kubernetes. Add the repository and install:

```bash title="Install Flagsmith on GKE"
helm repo add flagsmith https://flagsmith.github.io/flagsmith-charts/
helm install -n flagsmith --create-namespace flagsmith flagsmith/flagsmith \
  -f values.yaml
```

A minimal `values.yaml` for GKE with an external Cloud SQL database looks like this:

```yaml title="values.yaml"
postgresql:
 enabled: false

databaseExternal:
 enabled: true
 urlFromExistingSecret:
  enabled: true
  name: flagsmith-database-credentials
  key: DATABASE_URL

api:
 secretKeyFromExistingSecret:
  enabled: true
  name: flagsmith-secret-key
  key: SECRET_KEY
 replicacount: 2

frontend:
 replicacount: 2

taskProcessor:
 enabled: true
```

Create the Kubernetes secrets separately:

```bash title="Create secrets"
kubectl -n flagsmith create secret generic flagsmith-database-credentials \
  --from-literal=DATABASE_URL="postgres://flagsmith:PASSWORD@CLOUD_SQL_IP:5432/flagsmith"

kubectl -n flagsmith create secret generic flagsmith-secret-key \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)"
```

:::warning

Do not use the in-cluster PostgreSQL for production deployments. Always use an externally managed database such as
[Cloud SQL for PostgreSQL](#database--cloud-sql-for-postgresql).

:::

For the full list of chart values — including ingress, PgBouncer, resource limits, and deployment strategy — see our
[Kubernetes and OpenShift deployment guide](/deployment-self-hosting/hosting-guides/kubernetes-openshift).

The chart source is available on GitHub: [Flagsmith Helm Charts](https://github.com/Flagsmith/flagsmith-charts).

### Database — Cloud SQL for PostgreSQL

We recommend [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres) as the database for Flagsmith on
GCP.

- **PostgreSQL version:** We run our SaaS platform on PostgreSQL 15. Versions 12 and above are supported.
- **High availability:** Enable [regional HA](https://cloud.google.com/sql/docs/postgres/high-availability) for
  production workloads.
- **Connectivity:** Use [private IP](https://cloud.google.com/sql/docs/postgres/connect-instance-private-ip) or the
  [Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-kubernetes-engine) to connect from GKE.
- **Connection pooling:** For high-traffic deployments, enable PgBouncer via the Helm chart. See the
  [PgBouncer section](/deployment-self-hosting/hosting-guides/kubernetes-openshift#pgbouncer) in our Kubernetes guide.

When starting for the first time, Flagsmith will create the database schema automatically. Schema upgrades happen
seamlessly during application server upgrades.

### Terraform

:::info

Terraform modules for provisioning GKE and Cloud SQL for Flagsmith deployments are planned. In the meantime, you can use
the Helm chart to deploy Flagsmith onto an existing GKE cluster.

:::

---

## Cloud Run (Quick Start)

:::note

Cloud Run is well suited for evaluation and smaller deployments. For production and enterprise workloads, we recommend
[GKE with Helm charts](#gke-recommended-for-production).

:::

We recommend running the [unified Docker image](https://hub.docker.com/repository/docker/flagsmith/flagsmith) on Cloud
Run.

Study our [docker-compose file](https://github.com/Flagsmith/flagsmith/blob/main/docker-compose.yml) to understand the
base environment variables. All available environment variables are
[documented here](/deployment-self-hosting/core-configuration/environment-variables).

Run a single Cloud Run service with at least
[2 minimum instances](https://cloud.google.com/run/docs/configuring/min-instances) to avoid cold starts, particularly
for serving low-latency requests to the SDKs. For more sizing information, see our
[scaling page](/deployment-self-hosting/scaling-and-performance/sizing-and-scaling).

Use `/health` as the health-check endpoint for both the API and the frontend.

For the database, use [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres). We support PostgreSQL
versions 12 and above; our SaaS platform runs on version 15.

:::tip

When your deployment grows beyond evaluation, consider migrating to
[GKE with Helm charts](#gke-recommended-for-production) for better control over scaling, networking, and operations.

:::
