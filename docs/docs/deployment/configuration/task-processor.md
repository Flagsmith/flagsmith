# Asynchronous Task Processor

Flagsmith has the ability to consume asynchronous tasks using a separate task processor service. If flagsmith is run
without the asynchronous processor, the flagsmith API will run any asynchronous tasks in a separate, unmanaged thread.

## Running the Processor

The task processor can be run using the `flagsmith/flagsmith-api` image with a slightly different entrypoint. It can be
pointed to the same database that the API container is using, or instead, [it can use a separate
database](#running-the-processor-with-a-separate-database) as broker and result storage.

To enable the API sending tasks to the processor, you must set the `TASK_RUN_METHOD` environment variable to
`"TASK_PROCESSOR"` in the `flagsmith` container running the Flagsmith application.

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
  - 8000:8000
 depends_on:
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

## Running the Processor with a Separate Database

The task processor can be run with a separate database for the task queue and results, which can be useful to separate
infrastructure concerns. To do this, you need point the application — i.e. both the API and task processor services —
to a different database than the primary database used by the API. This can be done in **one of the following ways:**

- Set the `TASK_PROCESSOR_DATABASE_URL` environment variable pointing to the task processor database.
- Set the old-style environment variables `TASK_PROCESSOR_DATABASE_HOST`, `TASK_PROCESSOR_DATABASE_PORT`,
  `TASK_PROCESSOR_DATABASE_USER`, `TASK_PROCESSOR_DATABASE_PASSWORD`, `TASK_PROCESSOR_DATABASE_NAME` to point to the
  task processor database.

A basic docker-compose setup with a separate database might look like:

```yaml
api_database:
 image: postgres:15.5-alpine
 environment:
  POSTGRES_PASSWORD: password
  POSTGRES_DB: flagsmith
 container_name: flagsmith_api_database

task_processor_database:
 image: postgres:15.5-alpine
 environment:
  POSTGRES_PASSWORD: password
  POSTGRES_DB: flagsmith_task_processor
 container_name: flagsmith_task_processor_database

flagsmith:
 image: flagsmith/flagsmith-api:latest
 environment:
  DJANGO_ALLOWED_HOSTS: '*'
  DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
  TASK_PROCESSOR_DATABASE_URL: postgresql://postgres:password@task_processor_database:5432/flagsmith_task_processor
  ENV: prod
  TASK_RUN_METHOD: TASK_PROCESSOR
 ports:
  - 8000:8000
 depends_on:
  - api_database
  - task_processor_database

flagsmith_processor:
 image: flagsmith/flagsmith-api:latest
 environment:
  DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
  TASK_PROCESSOR_DATABASE_URL: postgresql://postgres:password@task_processor_database:5432/flagsmith_task_processor
 command:
  - run-task-processor
 depends_on:
  - flagsmith
  - api_database
  - task_processor_database
```

### Migrating from the Default Database (or back)

After pointing the task processor to a different database, or back to the default database, the application will do its
best effort to consume tasks from the previous storage, as to ensure no tasks are lost.

All task processor data stored in the previous database **remains intact**, as updating settings will not automatically
move the data between databases. Optionally, you may want to run the following command to migrate the data:

```bash
docker-compose run flagsmith python manage.py move_task_processor_data --source-db default --target-db task_processor  # or vice versa
```

Note that this command will attempt to **destroy** task processor data from the source database after copying it to the
target database, which might fail if the application is running and updating task processor data at the same time. This
behavior can be disabled by passing the `--no-destroy` flag to the command.

```bash
docker-compose run flagsmith python manage.py move_task_processor_data --source-db default --target-db task_processor --no-destroy  # or vice versa
```

This utility assumes that there is no other task processor data in the target database. It is expected to error out if
any task processor data already exists in the target database.

## Monitoring

There are a number of options for monitoring the task processor's health.

### Health checks

A task processor container exposes `/health/readiness` and `/health/liveness` endpoints for readiness and liveness
probes. The endpoints run simple availability checks. To include a test that enqueues a task and makes sure it's run
to your readiness probe, set `ENABLE_TASK_PROCESSOR_HEALTH_CHECK` environment variable to `True`.

### Task statistics

Both API and task processor expose an endpoint which returns task processor statistics in JSON format.
This endpoint is available at `GET /processor/monitoring`. See an example response below:

```json
{
 "waiting": 1  // The number of tasks waiting in the queue.
}
```
