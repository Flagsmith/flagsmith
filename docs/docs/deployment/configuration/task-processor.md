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
        image: flagsmith/flagsmith-api
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
       build:
           dockerfile: api/Dockerfile
           context: .
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
options are via command line arguments when starting the processor.

| Argument            | Description                                                               | Default |
| ------------------- | ------------------------------------------------------------------------- | ------- |
| `--sleepintervalms` | The amount of ms each worker should sleep between checking for a new task | 2000    |
| `--numthreads`      | The number of worker threads to run per task processor instance           | 5       |
| `--graceperiodms`   | The amount of ms before a worker thread is considered 'stuck'.            | 20000   |

## Monitoring

There are a number of options for monitoring the task processor's health.

### Checking Thread / Worker Health

The task processor includes a management command which checks the health of the worker threads which are running tasks.

```
python manage.py checktaskprocessorthreadhealth
```

The command will exit with either a success exit code (0) or a failure exit code (1).

### API to Task Processor health

To monitor that the API can send tasks to the processor and that they are successfully run, there is a custom health
check which can be enabled on the general health endpoint (`GET /health?format=json`). This health check needs to be
enabled manually, which can be done by setting the `ENABLE_TASK_PROCESSOR_HEALTH_CHECK` environment variable to `True`
(in the flagsmith application container, not the task processor). Note that this health check is not considered
"critical" and hence, the endpoint will return a 200 OK regardless of whether the task processor is sucessfully
processing tasks or not.

### Task statistics

Within the API, there is an endpoint which returns, in JSON format, statistics about the tasks consumed / to be consumed
by the processor. This endpoint is available at `GET /processor/monitoring`. This will respond with the following data:

```json
{
 "waiting": 1
}
```
