---
title: Monitoring
description: Setting up monitoring integrations like AppDynamics and StatsD.
---

Monitoring your Flagsmith instance is crucial for keeping things running smoothly, spotting issues early, and making sure your platform is performing as expected. Whether you're running a small self-hosted setup or a large-scale deployment, having the right monitoring tools in place will help you keep tabs on system health, performance, and usage.

This page covers how to integrate Flagsmith with popular monitoring solutions like AppDynamics and StatsD. We'll walk you through the setup steps and share some tips for getting the most out of your monitoring stack.

## AppDynamics

:::info

AppDynamics is an Enterprise only feature.

:::

The application supports the use of AppDynamics for monitoring purposes. In order to set up AppDynamics for your environment, follow the steps below:

:::note

There is a bug in the AppDynamics wizard that sets the value `ssl = (on)` which needs to be changed to `ssl = on`

:::

1. Set up your application in your AppDynamics dashboard using the "Getting Started Wizard - Python".
2. In the wizard, you will need to select the "uWSGI with Emperor: Module Directive" when choosing a deployment method.
3. On completing the wizard, you will be provided with a configuration file like the one seen here in the appdynamics.template.cfg provided, except with your application information. Make a copy of this information and place it in a file.

### Running with Docker

When running with traditional Docker, you can use the code snippet below to inject the required information for running AppDynamics:

```shell
docker run -t \{image_name\} -v \{config_file_path\}:/etc/appdynamics.cfg -e APP_DYNAMICS=on
```

Replacing the values for:

- **\{image_name\}**: the tagged name of the Docker image you are using
- **\{config_file_path\}**: the absolute path of the appdynamics.cfg file on your system

### Running with Docker Compose

When running with the `docker-compose.yml` file provided, ensure the `APP_DYNAMICS` environment variable is set to `on` as seen below:

```yaml
api:
 build:
 context: .
 dockerfile: docker/Dockerfile
 env:
  APP_DYNAMICS: 'on'
 volumes:
  - \{config_file_path\}:/etc/appdynamics.cfg
```

Replacing the value for **\{config_file_path\}** with the absolute path of the appdynamics.cfg file on your system.

Running the command below will build the Docker image with all the AppDynamics config included:

```shell
docker-compose -f docker-compose.yml build
```

This image can then be run locally using the docker-compose `up` command as seen below:

```shell
docker-compose -f docker-compose.yml up
```

### Additional Settings

If you need additional AppDynamics setup options, you can find the other environment variables you can set [here](https://docs.appdynamics.com/display/PRO21/Python+Agent+Settings).

## Prometheus

To enable the Prometheus `/metrics` endpoint, set the `PROMETHEUS_ENABLED` environment variable to `true`.

The metrics provided by Flagsmith are described below.

| Metric Name | Type | Description | Labels |
|-------------|------|-------------|--------|
| `flagsmith_build_info` | Gauge | Flagsmith version and build information | `ci_commit_sha`, `version` |
| `flagsmith_environment_document_cache_queries` | Counter | Results of cache retrieval for environment document. `result` label is either `hit` or `miss` | `result` |
| `flagsmith_http_server_request_duration_seconds` | Histogram | HTTP request duration in seconds | `route`, `method`, `response_status` |
| `flagsmith_http_server_requests` | Counter | Total number of HTTP requests | `route`, `method`, `response_status` |
| `flagsmith_http_server_response_size_bytes` | Histogram | HTTP response size in bytes | `route`, `method`, `response_status` |
| `flagsmith_task_processor_enqueued_tasks` | Counter | Total number of enqueued tasks | `task_identifier` |
| `flagsmith_task_processor_finished_tasks` | Counter | Total number of finished tasks. Only collected by Task Processor. `task_type` label is either `recurring` or `standard` | `task_identifier`, `task_type`, `result` |
| `flagsmith_task_processor_task_duration_seconds` | Histogram | Task processor task duration in seconds. Only collected by Task Processor. `task_type` label is either `recurring` or `standard` | `task_identifier`, `task_type`, `result` |

## StatsD

There is currently no specific documentation for setting up StatsD.

## Task Processor Monitoring

There are a number of options for monitoring the task processor's health.

### Health Checks

A task processor container exposes `/health/readiness` and `/health/liveness` endpoints for readiness and liveness probes. The endpoints run simple availability checks. To include a test that enqueues a task and makes sure it's run to your readiness probe, set `ENABLE_TASK_PROCESSOR_HEALTH_CHECK` environment variable to `True`.

### Task Statistics

Both API and task processor expose an endpoint which returns task processor statistics in JSON format. This endpoint is available at `GET /processor/monitoring`. See an example response below:

```json
{
 "waiting": 1  // The number of tasks waiting in the queue.
}
```
