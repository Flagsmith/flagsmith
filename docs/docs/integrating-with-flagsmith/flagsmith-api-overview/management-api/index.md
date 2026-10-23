---
title: Management API
sidebar_label: Management API
---

The Management API allows you to programmatically manage your Flagsmith projects, environments, features, segments, and users. Essentially, any action you can perform in the Flagsmith dashboard can also be accomplished via the Management API.

This API is designed for automation, integrations, and building custom workflows on top of Flagsmith.

You do not need administrator privileges to use it. Requests act with the permissions of the API key or user
making them, so any member of an organisation can use the Management API within the scope of their
[permissions](/administration-and-security/access-control/rbac).

## API Explorer

You can explore the full Management API via Swagger at [https://api.flagsmith.com/api/v1/docs/](https://api.flagsmith.com/api/v1/docs/). You can also get the OpenAPI specification in [JSON](https://api.flagsmith.com/api/v1/swagger.json) or [YAML](https://api.flagsmith.com/api/v1/swagger.yaml) format.

We also have a [Postman Collection](https://www.postman.com/flagsmith/workspace/flagsmith/overview) that you can use to experiment with the API.

:::info
Our Management API has a [Rate Limit](/administration-and-security/governance-and-compliance/system-limits#management-api-rate-limit) that you should be aware of.
::: 