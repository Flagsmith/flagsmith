---
title: Code Examples
sidebar_label: Code Examples
---

Here is a simple example of how to use the Admin API with `curl` to create a new Environment within a Project.

```bash
curl 'https://api.flagsmith.com/api/v1/environments/' \
    -H 'Content-Type: application/json' \
    -H 'Authorization: Api-Key <API TOKEN FROM ORGANISATION PAGE>' \
    --data-binary '{"name":"New Environment","project":"<Project ID>"}'
```

### Parameters

-   `Authorization`: Your Organisation API Token, prefixed with `Api-Key`.
-   `Content-Type`: `application/json`
-   `--data-binary`: The JSON payload containing the details of the environment you want to create. You'll need to provide the `name` for the new environment and the `project` ID it belongs to.

For more complex examples and different languages, please refer to the full code examples in the [original REST API documentation](../../../clients/rest/#code-examples). 