---
description: Manage your Feature Flags and Remote Config in your REST APIs.
sidebar_label: REST
sidebar_position: 2
---

# Direct API Access

:::tip

Some API actions require object UUIDs/IDs to be referenced. You can enable the [JSON View](#json-view) from your account
settings page which will help you access these variables.

:::

:::info

Our Admin API has a [Rate Limit](/system-administration/system-limits#admin-api-rate-limit) that you need to be aware
of.

:::

## Overview

Our API is split in two :

1. The `Public SDK API` that serves Flags to your client applications. This API does not require secret keys and is open
   by design.
2. The `Private Admin API` that allows you to do things like programatically create and toggle flags. Interacting with
   this API requires a [secret key](#private-admin-api-endpoints).

## API Explorer

You can view the API via Swagger at [https://api.flagsmith.com/api/v1/docs/](https://api.flagsmith.com/api/v1/docs/) or
get OpenAPI as [JSON](https://api.flagsmith.com/api/v1/docs/?format=.json) or
[YAML](https://api.flagsmith.com/api/v1/docs/?format=.yaml).

We have a [Postman Collection](https://www.postman.com/flagsmith/workspace/flagsmith/overview) that you can use to play
around with the API and get a feel for how it works.

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/14712118-a638325a-f1f4-4570-8b4d-fd2841218dfa?action=collection%2Ffork&collection-url=entityId%3D14712118-a638325a-f1f4-4570-8b4d-fd2841218dfa%26entityType%3Dcollection%26workspaceId%3D452554eb-f581-4754-b5b8-0deabdce9f4b#?env%5BFlagsmith%20Environment%5D=W3sia2V5IjoiRmxhZ3NtaXRoIEVudmlyb25tZW50IEtleSIsInZhbHVlIjoiOEt6RVRkRGVNWTd4a3FrU2tZM0dzZyIsImVuYWJsZWQiOnRydWV9LHsia2V5IjoiYmFzZVVybCIsInZhbHVlIjoiaHR0cHM6Ly9hcGkuZmxhZ3NtaXRoLmNvbS9hcGkvdjEvIiwiZW5hYmxlZCI6dHJ1ZX0seyJrZXkiOiJJZGVudGl0eSIsInZhbHVlIjoicG9zdG1hbl91c2VyXzEyMyIsImVuYWJsZWQiOnRydWV9XQ==)

You can also access the API directly with tools like [curl](https://curl.haxx.se/) or [httpie](https://httpie.org/), or
with clients for languages that we do not currently have SDKs for.

## API Keys

### Public SDK API Endpoints

Publicly accessible API calls need to have an environment key supplied with each request. This is provided as an HTTP
header, with the name `X-Environment-Key` and the value of the Environment Key that you can find within the Flagsmith
administrative area.

For SaaS customers, the URL to hit for this API is [`https://edge.api.flagsmith.com/`](/advanced-use/edge-api).

### Private Admin API Endpoints

You can also do things like create new flags, environments, toggle flags or indeed anything that is possible from the
administrative front end via the API.

To authenticate, you can use the API Token associated with your Organisation. This can be found in the `Organisation`
page from the top navigation panel. You need to create a token and then provide it as an HTTP header:

```bash
Authorization: Api-Key <API TOKEN FROM ORGANISATION PAGE>
```

For example, to create a new Environment:

```bash
curl 'https://api.flagsmith.com/api/v1/environments/' \
    -H 'content-type: application/json' \
    -H 'authorization: Api-Key <API TOKEN FROM ORGANISATION PAGE>' \
    --data-binary '{"name":"New Environment","project":"<Project ID>"}'
```

You can find a complete list of endpoints via the Swagger REST API at
[https://api.flagsmith.com/api/v1/docs/](https://api.flagsmith.com/api/v1/docs/).

For SaaS customers, the URL to hit for this API is `https://api.flagsmith.com/`.

## Curl Examples

These are the two main endpoints that you need to consume the SDK aspect of the API.

### Get Environment Flags

```bash
curl 'https://edge.api.flagsmith.com/api/v1/flags/' -H 'X-Environment-Key: <Your Env Key>'
```

### Send Identity with Traits and receive Flags

This command will perform the entire SDK Identity workflow in a single call:

1. Lazily create an Identity
2. Setting Traits for the Identity
3. Receiving the Flags for that Identity

```bash
curl --request POST 'https://edge.api.flagsmith.com/api/v1/identities/' \
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

## JSON View

You can enable the JSON view in your Account Settings page. This will then give you access to relevant object meta data
in the Flag area of the dashboard.

## Code Examples

Below are some examples for achieving certain actions with the REST API, using python.

### Create a feature

```python
import os

from requests import Session

API_URL = os.environ.get("API_URL", "https://api.flagsmith.com/api/v1")  # update this if self-hosting
PROJECT_ID = os.environ["PROJECT_ID"]  # obtain this from the URL on your dashboard
TOKEN = os.environ["API_TOKEN"]  # obtain this from the account page in your dashboard
FEATURE_NAME = os.environ["FEATURE_NAME"]  # name of the feature to create

session = Session()
session.headers.update({"Authorization": f"Token {TOKEN}"})

create_feature_url = f"{API_URL}/projects/{PROJECT_ID}/features/"
data = {"name": FEATURE_NAME}
response = session.post(create_feature_url, json=data)
```

### Update the value / state of a feature in an environment

```python
import json
import os

import requests

TOKEN = os.environ.get("API_TOKEN")  # obtained from Account section in dashboard
ENV_KEY = os.environ.get("ENV_KEY")  # obtained from environment settings in dashboard
BASE_URL = "https://api.flagsmith.com/api/v1"  # update this if self hosting
FEATURE_STATES_URL = f"{BASE_URL}/environments/{ENV_KEY}/featurestates"
FEATURE_NAME = os.environ.get("FEATURE_NAME")

session = requests.Session()
session.headers.update(
    {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}
)

# get the existing feature state id based on the feature name
get_feature_states_response = session.get(
    f"{FEATURE_STATES_URL}/?feature_name={FEATURE_NAME}"
)
feature_state_id = get_feature_states_response.json()["results"][0]["id"]

# update the feature state
data = {"enabled": True, "feature_state_value": "new value"}  # `feature_state_value` can be str, int or bool
update_feature_state_response = session.patch(
    f"{FEATURE_STATES_URL}/{feature_state_id}/", data=json.dumps(data)
)
```

### Create a segment and segment override

```python
import os

from requests import Session

API_URL = os.environ.get("API_URL", "https://api.flagsmith.com/api/v1")  # update this if self-hosting
SEGMENT_NAME = os.environ["SEGMENT_NAME"]  # define the name of the segment here
PROJECT_ID = os.environ["PROJECT_ID"]  # obtain this from the URL on your dashboard
TOKEN = os.environ["API_TOKEN"]  # obtain this from the account page in your dashboard
FEATURE_ID = os.environ.get("FEATURE_ID")  # obtain this from the URL on your dashboard when viewing a feature
IS_FEATURE_SPECIFIC = os.environ.get("IS_FEATURE_SPECIFIC", default=False) == "True"  # set this to True to create a feature specific segment
ENVIRONMENT_ID = os.environ["ENVIRONMENT_ID"]  # must (currently) be obtained by inspecting the request to /api/v1/environments in the network console

# set these values to create a segment override for the segment, feature, environment combination
ENABLE_FOR_SEGMENT = os.environ.get("ENABLE_FOR_SEGMENT", default=False) == "True"
VALUE_FOR_SEGMENT = os.environ.get("VALUE_FOR_SEGMENT")

SEGMENT_DEFINITION = {
    "name": SEGMENT_NAME,
    "feature": FEATURE_ID if IS_FEATURE_SPECIFIC else None,
    "project": PROJECT_ID,
    "rules": [
        {
            "type": "ALL",
            "rules": [  # add extra rules here to build up 'AND' logic
                {
                    "type": "ANY",
                    "conditions": [  # add extra conditions here to build up 'OR' logic
                        {
                            "property": "my_trait",  # specify a trait key that you want to match on, e.g. organisationId
                            "operator": "EQUAL",  # specify the operator you want to use (one of EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN, GREATER_THAN_INCLUSIVE, LESS_THAN_INCLUSIVE, CONTAINS, NOT_CONTAINS, REGEX, PERCENTAGE_SPLIT, IS_SET, IS_NOT_SET)
                            "value": "my-value"  # the value to match against, e.g. 103
                        }
                    ]
                }
            ]
        }
    ]
}

session = Session()
session.headers.update({"Authorization": f"Token {TOKEN}"})

# first let's create the segment
create_segment_url = f"{API_URL}/projects/{PROJECT_ID}/segments/"
create_segment_response = session.post(create_segment_url, json=SEGMENT_DEFINITION)
assert create_segment_response.status_code == 201
segment_id = create_segment_response.json()["id"]

if not any(key in os.environ for key in ("ENABLE_FOR_SEGMENT", "VALUE_FOR_SEGMENT")):
    print("Segment created! Not creating an override as no state / value defined.")
    exit(0)

# next we need to create a feature segment (a flagsmith internal entity)
create_feature_segment_url = f"{API_URL}/features/feature-segments/"
feature_segment_data = {
    "feature": FEATURE_ID,
    "segment": segment_id,
    "environment": ENVIRONMENT_ID
}
create_feature_segment_response = session.post(create_feature_segment_url, json=feature_segment_data)
assert create_feature_segment_response.status_code == 201
feature_segment_id = create_feature_segment_response.json()["id"]

# finally, we can create the segment override
create_segment_override_url = f"{API_URL}/features/featurestates/"
feature_state_data = {
    "feature": FEATURE_ID,
    "feature_segment": feature_segment_id,
    "environment": ENVIRONMENT_ID,
    "enabled": ENABLE_FOR_SEGMENT,
    "feature_state_value": {
        "type": "unicode",
        "string_value": VALUE_FOR_SEGMENT
    }
}
create_feature_state_response = session.post(create_segment_override_url, json=feature_state_data)
assert create_feature_state_response.status_code == 201
```

### Update a segment's rules

```python
import os

from requests import Session

API_URL = os.environ.get("API_URL", "https://api.flagsmith.com/api/v1")  # update this if self-hosting
PROJECT_ID = os.environ["PROJECT_ID"]  # obtain this from the URL on your dashboard
TOKEN = os.environ["API_TOKEN"]  # obtain this from the account page in your dashboard
SEGMENT_ID = os.environ.get("SEGMENT_ID")  # obtain this from the URL on your dashboard when viewing a segment

SEGMENT_RULES_DEFINITION = {
    "rules": [
        {
            "type": "ALL",
            "rules": [
                {
                    "type": "ANY",
                    "conditions": [  # add as many conditions here to build up a segment
                        {
                            "property": "my_trait",  # specify a trait key that you want to match on, e.g. organisationId
                            "operator": "EQUAL",  # specify the operator you want to use (one of EQUAL, NOT_EQUAL, GREATER_THAN, LESS_THAN, GREATER_THAN_INCLUSIVE, LESS_THAN_INCLUSIVE, CONTAINS, NOT_CONTAINS, REGEX, PERCENTAGE_SPLIT, IS_SET, IS_NOT_SET)
                            "value": "my-value"  # the value to match against, e.g. 103
                        }
                    ]
                }
            ]
        }
    ]
}

session = Session()
session.headers.update({"Authorization": f"Token {TOKEN}"})

update_segment_url = f"{API_URL}/projects/{PROJECT_ID}/segments/{SEGMENT_ID}/"
session.patch(update_segment_url, json=SEGMENT_RULES_DEFINITION)
```

### Iterate over Identities

Sometimes it can be useful to iterate over your Identities to check things like Segment overrides.

```python
import os

import requests

TOKEN = os.environ.get("API_TOKEN")  # obtained from Account section in dashboard
ENV_KEY = os.environ.get("ENV_KEY")  # obtained from Environment settings in dashboard
BASE_URL = "https://api.flagsmith.com/api/v1"  # update this if self hosting
IDENTITIES_PAGE_URL = f"{BASE_URL}/environments/{ENV_KEY}/edge-identities/?page_size=20"

session = requests.Session()
session.headers.update(
    {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}
)

# get the existing feature state id based on the feature name
page_of_identities = session.get(f"{IDENTITIES_PAGE_URL}")
print(page_of_identities.json())

for identity in page_of_identities.json()['results']:
    print(str(identity))
    IDENTITY_UUID = identity['identity_uuid']
    IDENTITY_URL = f"{BASE_URL}/environments/{ENV_KEY}/edge-identities/{IDENTITY_UUID}/edge-featurestates/all/"
    identity_data = session.get(f"{IDENTITY_URL}")
    print(identity_data.json())
```

### Delete an Edge Identity

```python
import os

import requests

TOKEN = os.environ.get("API_TOKEN")  # obtained from Account section in dashboard
ENV_KEY = os.environ.get("ENV_KEY")  # obtained from Environment settings in dashboard
IDENTITY_UUDI = os.environ["IDENTITY_UUDI"] # must (currently) be obtained by inspecting the request to /api/v1/environments/{ENV_KEY}/edge-identities/{IDENTITY_UUDI} in the network console
BASE_URL = "https://edge.api.flagsmith.com/api/v1"  # update this if self hosting

session = requests.Session()
session.headers.update(
    {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}
)

# delete the existing edge identity based on the uuid
delete_edge_identity_url = f"{BASE_URL}/environments/{ENV_KEY}/edge-identities/{IDENTITY_UUDI}/"
delete_edge_identity_response = session.delete(delete_edge_identity_url)
assert delete_edge_identity_response.status_code == 204

```

### Delete an Identity

```python
import os

import requests

TOKEN = os.environ.get("API_TOKEN")  # obtained from Account section in dashboard
ENV_KEY = os.environ.get("ENV_KEY")  # obtained from Environment settings in dashboard
IDENTITY_ID = os.environ["IDENTITY_ID"] # obtain this from the URL on your dashboard when viewing an identity
BASE_URL = "https://api.flagsmith.com/api/v1"  # update this if self hosting

session = requests.Session()
session.headers.update(
    {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}
)

# delete the existing identity based on the identity id
delete_identity_url = f"{BASE_URL}/environments/{ENV_KEY}/identities/{IDENTITY_ID}/"
delete_identity_response = session.delete(delete_identity_url)
assert delete_identity_response.status_code == 204
```

### Bulk Uploading Identities and Traits

You can achieve this with a `POST` to the `identities` endpoint:

```bash
curl -X "POST" "https://edge.api.flagsmith.com/api/v1/identities/?identifier=<identity_id>" \
     -H 'X-Environment-Key: <Your Environment Key>' \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "traits":   "traits": [
    {
      "trait_key": "this_key",
      "trait_value": "this_value"
    },
    {
      "trait_key": "this_key2",
      "trait_value": "this_value2"
    }
  ],
  "identifier": "<identity_id>"
}'
```
