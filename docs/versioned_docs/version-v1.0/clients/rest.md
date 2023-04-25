---
description: Manage your Feature Flags and Remote Config in your REST APIs.
sidebar_label: REST
sidebar_position: 1
---

# Direct API Access

Flagsmith is built around a client/server architecture. The REST API server is accessible from SDK clients as well as
the administration front end. This decoupling means that you can programmatically access the entire API if you wish.

We have a [Postman Collection](https://www.postman.com/flagsmith/workspace/flagsmith/overview) that you can use to play
around with the API and get a feel for how it works.

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/14712118-a638325a-f1f4-4570-8b4d-fd2841218dfa?action=collection%2Ffork&collection-url=entityId%3D14712118-a638325a-f1f4-4570-8b4d-fd2841218dfa%26entityType%3Dcollection%26workspaceId%3D452554eb-f581-4754-b5b8-0deabdce9f4b#?env%5BFlagsmith%20Environment%5D=W3sia2V5IjoiRmxhZ3NtaXRoIEVudmlyb25tZW50IEtleSIsInZhbHVlIjoiOEt6RVRkRGVNWTd4a3FrU2tZM0dzZyIsImVuYWJsZWQiOnRydWV9LHsia2V5IjoiYmFzZVVybCIsInZhbHVlIjoiaHR0cHM6Ly9hcGkuZmxhZ3NtaXRoLmNvbS9hcGkvdjEvIiwiZW5hYmxlZCI6dHJ1ZX0seyJrZXkiOiJJZGVudGl0eSIsInZhbHVlIjoicG9zdG1hbl91c2VyXzEyMyIsImVuYWJsZWQiOnRydWV9XQ==)

You can also access the API directly with tools like [curl](https://curl.haxx.se/) or [httpie](https://httpie.org/), or
with clients for languages that we do not currently have SDKs for.

## API Explorer

You can view the API via Swagger at [https://api.flagsmith.com/api/v1/docs/](https://api.flagsmith.com/api/v1/docs/) or
get OpenAPI as [JSON](https://api.flagsmith.com/api/v1/docs/?format=.json) or
[YAML](https://api.flagsmith.com/api/v1/docs/?format=.yaml).

## Environment Key

Publicly accessible API calls need to have an environment key supplied with each request. This is provided as an HTTP
header, with the name `X-Environment-Key` and the value of the environment API key that you can find within the
Flagsmith administrative area.

### Curl Example

```bash
curl 'https://api.flagsmith.com/api/v1/flags/' -H 'X-Environment-Key: TijpMX6ajA7REC4bf5suYg'
```

### httpie Example

```bash
http GET 'https://api.flagsmith.com/api/v1/flags/' 'X-Environment-Key':'TijpMX6ajA7REC4bf5suYg'
```

## Private Endpoints

You can also do things like create new flags, environments, toggle flags or indeed anything that is possible from the
administrative front end via the API.

To authenticate, you can use the token associated with your account. This can be found in the "Account" page from the
top right navigation panel. Use this token for API calls. For example, to create a new evironment:

```bash
curl 'https://api.flagsmith.com/api/v1/environments/' \
    -H 'content-type: application/json' \
    -H 'authorization: Token <TOKEN FROM PREVIOUS STEP>' \
    --data-binary '{"name":"New Environment","project":"<Project ID>"}'
```

You can find a complete list of endpoints via the Swagger REST API at
[https://api.flagsmith.com/api/v1/docs/](https://api.flagsmith.com/api/v1/docs/).

## Useful SDK Endpoints

### Send Identity with Traits and receive Flags

This `curl` command below will perform the entire SDK workflow in a single call:

1. Creating an Identity
2. Setting Traits for the Identity
3. Receiving the Flags for that Identity

```bash
curl --request POST 'https://api.flagsmith.com/api/v1/identities/' \
--header 'X-Environment-Key: <Your Env Key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "identifier":"identifier_5",
    "traits": [
        {
            "trait_key": "my_trait_key",
            "trait_value": 123.5
        },
        {
            "trait_key": "my_other_key",
            "trait_value": true
        }
    ]
}'
```
