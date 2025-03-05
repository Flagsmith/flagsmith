# Asynchronous Task Processor

Flagsmith has the ability to consume asynchronous tasks using a separate task processor service. If flagsmith is run
without the asynchronous processor, the flagsmith API will run any asynchronous tasks in a separate, unmanaged thread.

## Running the Processor

The task processor can be run using the flagsmith/flagsmith-api image with a slightly different entrypoint. It should be
pointed to the same database that the API container is using. To enable the API sending tasks to the processor, you must
set the `TASK_RUN_METHOD` to `TASK_PROCESSOR` in the flagsmith container running the flagsmith application.

A basic docker-compose setup might look like:

```yaml
postgres:
 image: postgres:15.5-alpine
 environment:
  POSTGRES_PASSWORD: password
  POSTGRES_DB: flagsmith
 container_name: flagsmith_postgres

flagsmith:
 image: flagsmith/flagsmith-api:latest
 environment:
  DJANGO_ALLOWED_HOSTS: '*'
  DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
  ENV: prod
  TASK_RUN_METHOD: TASK_PROCESSOR
 ports:
  - '8000:8000'
 depends_on:
  - postgres
 links:
  - postgres

flagsmith_processor:
 image: flagsmith/flagsmith-api:latest
 environment:
  DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
 command:
  - run-task-processor
 depends_on:
  - flagsmith
  - postgres
```

## Configuring the Processor

The processor exposes a number of configuration options to tune the processor to your needs / setup. These configuration
options are via command line arguments when starting the processor. The default Flagsmith container entrypoint expects
these options as `TASK_PROCESSOR_`-prefixed environment variables.

| Environment variable               | Argument            | Description                                                                | Default |
| ---------------------------------- | ------------------- | -------------------------------------------------------------------------- | ------- |
| `TASK_PROCESSOR_SLEEP_INTERVAL_MS` | `--sleepintervalms` | The amount of ms each worker should sleep between checking for a new task. | 500     |
| `TASK_PROCESSOR_NUM_THREADS`       | `--numthreads`      | The number of worker threads to run per task processor instance.           | 5       |
| `TASK_PROCESSOR_GRACE_PERIOD_MS`   | `--graceperiodms`   | The amount of ms before a worker thread is considered 'stuck'.             | 20000   |
| `TASK_PROCESSOR_QUEUE_POP_SIZE`    | `--queuepopsize`    | The number of enqueued tasks to retrieve for processing for one iteration. | 10      |

## Monitoring

There are a number of options for monitoring the task processor's health.

### Health checks

A task processor container exposes `/health/readiness` and `/health/liveness` endpoints for readiness and liveness
probes. The endpoints run simple availability checks. To include a test that enqueues a task and makes sure it's run
to your readiness probe, set `ENABLE_TASK_PROCESSOR_HEALTH_CHECK` environment variable to `True`.

### Task statistics

Both API and Task processor expose an endpoint which returns Task processor statistics in JSON format.
This endpoint is available at `GET /processor/monitoring`. See an example response below:

```json
{
 "waiting": 1  // The number of tasks waiting in the queue.
}
```
