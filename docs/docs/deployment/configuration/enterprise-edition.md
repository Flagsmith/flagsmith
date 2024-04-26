---
sidebar_position: 4
---

# Enterprise Edition

Flagsmith is also provided as an "Enterprise Edition" which has additional features and capabilities over the Open
Source product:

- [Role Based Access Controls](/system-administration/rbac)
- [SAML](/system-administration/authentication/SAML), [OAuth](/system-administration/authentication/OAuth),
  [LDAP](/system-administration/authentication/LDAP), [ADFS](/system-administration/authentication/ADFS) and
  [Okta](/system-administration/authentication/Okta) authentication, as well as the ability to lock authentication to a
  single provider
- Additional database engines: Oracle, SQL Server and MySQL
- Additional deployment and orchestration options as detailed below

## Deployment Options

We currently support the following infrastructure platforms:

- Kubernetes
- Redhat OpenShift
- Amazon Web Services (AWS) - via
  [Amazon ECS](https://aws.amazon.com/ecs/?whats-new-cards.sort-by=item.additionalFields.postDateTime&whats-new-cards.sort-order=desc)
- Google Cloud Platform (GCP) - via [AppEngine](https://cloud.google.com/appengine)
- Azure - via [Container Instances](https://azure.microsoft.com/en-gb/services/container-instances/)

If you require additional deployment options, please contact us.

## Orchestration

We currently have the following orchestration options:

- [Pulumi](https://www.pulumi.com/) scripts for AWS deployments
- [Terraform](https://www.terraform.io/) scripts for AWS and GCP deployments
- [Helm Charts](https://helm.sh/) for Kubernetes deployments
- [Kubernetes Operator](https://operatorhub.io/operator/flagsmith) for Kubernetes Operator deployments

Please contact us for the relevant source code for these projects.

## Docker Image Repository

The Flagsmith API Enterprise Edition is hosted with a private Docker Hub repository. To access the Docker images in this
repository you will need to provide a Docker Hub account. Please get in touch if you need access to these repos.

We have 2 different Enterprise Edition Images. You can choose to use either image.

### "SaaS" image (flagsmith-private-cloud)

This image tracks our SaaS build and includes additional packages:

- SAML
- Workflows (Change Requests and Flag Scheduling)
- LDAP

This image also bundles the front end into the python application, meaning you don't need to run a separate front end
and back end.

### Enterprise Edition image (flagsmith-api-ee)

This image includes additions from the SaaS image above:

- Oracle Support
- MySQL Support
- Appdynamics Integration

## Environment Variables

### Frontend Environment Variables

| Variable                 | Example Value                | Description                                                                                                                           |
| ------------------------ | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **API_URL**              | http://localhost:8888/api/v1 | The URL of the API Backend                                                                                                            |
| **FLAGSMITH_CLIENT_API** | http://localhost:8888/api/v1 | This is where the features for the front end themselves are pulled from. Create a project within your backend and refer to flag names |

Env Var: **FLAGSMITH** Value example: 4vfqhypYjcPoGGu8ByrBaj Description: The `environment id` for the
`FLAGSMITH_CLIENT_API` project above.

### Version Tags

The versions of all of our enterprise images track the versions of our Open Source version. You can view these tags
here:

[https://github.com/Flagsmith/flagsmith/tags](https://github.com/Flagsmith/flagsmith/tags)

## AppDynamics

The application supports the use of AppDynamics for monitoring purposes. In order to set up AppDynamics for your
environment follow the steps below:

:::note

There is a bug in the AppDynamics wizard that sets the value `ssl = (on)` which needs to be changed to `ssl = on`

:::

1. Set up your application in your AppDynamics dashboard using the "Getting Started Wizard - Python".
2. In the wizard you will need to select the "uWSGI with Emperor: Module Directive" when choosing a deployment method
3. On completing the wizard you will be provided with a configuration file like the one seen here in the
   appdynamics.template.cfg provided, except with your application information. Make a copy of this information and
   place it in a file.

### Running with docker

When running with traditional Docker you can use the code snippet below to inject the required information for running
App Dynamics

```shell
docker run -t \{image_name\} -v \{config_file_path\}:/etc/appdynamics.cfg -e APP_DYNAMICS=on
```

Replacing the values for:

- **_\{image_name\}_**: the tagged name of the docker image you are using
- **_\{config_file_path\}_**: the absolute path of the appdynamics.cfg file on your system

### Running with docker-compose

When running with the `docker-compose.yml` file provided ensure the `APP_DYNAMICS` environment variable is set to `on`
as seen below:

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

Replacing the value for **_\{config_file_path\}_** with the absolute path of the appdynamics.cfg file on your system.

Running the command below will build the docker image with all the AppDynamics config included

```shell
docker-compose -f docker-compose.yml build
```

This image can then be run locally using the docker-compose `up` command as seen below

```shell
docker-compose -f docker-compose.yml up
```

### Additional settings

If you need additional AppDynamics setup options you can find the other environment variables you can set
[here](https://docs.appdynamics.com/display/PRO21/Python+Agent+Settings).

### Oracle Database

Flagsmith is compatible with the Oracle database engine by configuring a few environment variables correctly. Firstly,
you'll need to ensure that you have a value for `DJANGO_DB_ENGINE` set as `oracle`. Then you can set the remaining
database parameters (`DJANGO_DB_*`) as required.

#### Local Testing

The following sections detail how to run the application locally using the OracleDB Docker image. If you're looking to
run the application using an instance of OracleDB elsewhere, you just need to setup the environment variables correctly
as per the documentation.

:::note

**Prerequisites**

You will likely need to install the Oracle client on the machine running the Flagsmith API application. The instructions
to do so are [here](https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html).

:::

To run the application locally using Oracle (via Docker), you need to go through a registration with your docker hub
account to get access to the images. Go to https://hub.docker.com/_/oracle-database-enterprise-edition and register.
Once you've done that, you can run the Oracle database using docker, and we've created a docker-compose file to simplify
this.

```bash
docker-compose -f docker-compose.oracle.yml up db
```

Once you have a database running, you'll need to set up the database and users correctly. This can be done with the
following processes.

First, connect to the database itself:

```bash
sqlplus /nolog
```

OR

```bash
docker-compose exec db bash -c "source /home/oracle/.bashrc; sqlplus /nolog"
```

Once connected, you'll need to run the following SQL commands. Note that these commands should be amended if you'd like
a different password / user combination.

```sql
conn sys as sysdba;
# password is blank when asked
alter session set "_ORACLE_SCRIPT"=true;
create user oracle_user identified by oracle_password;
grant dba to oracle_user;
GRANT EXECUTE ON SYS.DBMS_LOB TO oracle_user;
GRANT EXECUTE ON SYS.DBMS_RANDOM TO oracle_user;
```

## Load testing

### JMeter

There are [JMeter](https://jmeter.apache.org/) tests avaiable in our public repo on GitHub:

https://github.com/Flagsmith/flagsmith/tree/main/api/jmeter-tests

### wrk

We also recommend using [wrk](https://github.com/wg/wrk) for load testing the core SDK endpoints. Some examples of this
(make sure you update URL and environment keys!)

```bash
#  Get flags endpoint
wrk -t6 -c200 -d20s -H 'X-Environment-Key: iyiS5EDNDxMDuiFpHoiwzG' http://127.0.0.1:8000/api/v1/flags/

# Get flags for an identity
wrk -t6 -c200 -d20s -H 'X-Environment-Key: iyiS5EDNDxMDuiFpHoiwzG' "http://127.0.0.1:8000/api/v1/identities/?identifier=mrflags@flagsmith.com"
```

## Common Installation Issues and Fixes

### Front end build errors with npm ERR! errno 137

This is an out of memory error. Start the container with more RAM.
