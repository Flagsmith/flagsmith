---
title: Troubleshooting
sidebar_label: Troubleshooting
sidebar_position: 90
---

Here are some common issues encountered when trying to set up Flagsmith in a self hosted environment.

## Health Checks

If you are using health-checks, make sure to use `/health` as the health-check endpoint for both the API and the Front
end.

## API and Database connectivity

The most common cause of issue when setting things up in AWS with an RDS database is missing Security Group permissions
between the API application and the RDS database. You need to ensure that the attached security groups for
ECS/Fargate/EC2 allow access to the RDS database.
[AWS provide more detail about this here](https://aws.amazon.com/premiumsupport/knowledge-center/ecs-task-connect-rds-database/)
and [here](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Overview.RDSSecurityGroups.html).

Make sure you have a `DATABASE_URL` environment variable set within the API application.

## Frontend > API DNS Setup

If you are running the API and the Front end as separate applications, you need to make sure that the Front end is
pointing to the API. Check the
[Front end environment variables](/deployment/hosting/locally-frontend#environment-variables), particularly `API_URL`.
