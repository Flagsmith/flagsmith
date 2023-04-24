# Edge Proxy

:::tip

The Edge Proxy is only available as part of our Enterprise Plans. Please
[get in touch](https://flagsmith.com/contact-us/) if this is something you are interested in!

:::

The Flagsmith Edge Proxy allows you to run an instance of the Flagsmith Engine close to your servers. If you are running
Flagsmith within a server-side environment, and you need very low latency response times, the Edge Proxy is for you!

The Edge Proxy runs as a lightweight Docker container. It connects to the core Flagsmith API (either powered by us at
api.flagsmith.com or self hosted by you) to get Environment Flags and Segment rules. You can then point the Flagsmith
SDKs to your Edge Proxy; it implements all the current SDK endpoints. This means you can serve a very large number of
requests close to your infrastructure and users, at very low latency. Check out the [architecture below](#architecture).

The Proxy also acts as a local cache, allowing you to make requests to the Proxy without hitting the core API.

## Performance

The Edge Proxy can currently serve ~2,000 requests per second at a mean latency of ~7ms on a single, 4-core VM. It is
stateless and hence close to perfectly scalable being deployed behind a load balancer.

## Running the Edge Proxy

The Edge Proxy runs as a docker container. It is currently available at the
[Docker Hub](https://hub.docker.com/repository/docker/flagsmith/edge-proxy).

:::tip

The `flagsmith/edge-proxy` image is private - please [get in touch](https://flagsmith.com/contact-us/) if you would like
access to it.

:::

```bash
# Download the Docker Image
docker pull flagsmith/edge-proxy

# Run it
docker run \
    -e FLAGSMITH_API_URL='https://api.flagsmith.com/api/v1/' \
    -e FLAGSMITH_API_TOKEN='<API Token - see below>' \
    -e ENVIRONMENT_API_KEYS='<Flagsmith Environment Key - see below>' \
    -p 8000:8000 \
    flagsmith/edge-proxy:latest
```

The Proxy is now running and available on port 8000.

### Environment Variables

You can configure the Edge Proxy with the following Environment Variables:

- `FLAGSMITH_API_URL` **Required**. The URL of the API to proxy e.g. `https://api.flagsmith.com/api/v1/` or your own
  domain name if you are self hosting the Flagsmith API.
- `ENVIRONMENT_API_KEYS` **Required**. A list of Environment keys to serve. Provided as a comma-separated String e.g.
  `4vfqhypYjcPoGGu8ByrBaj, EmJFz265Q6CAXuGRZYnkeE, "8KzETdDeMY7xkqkSkY3Gsg`
- `FLAGSMITH_API_TOKEN` **Required**. Can be retrieved as per [these instructions](/clients/rest.md##private-endpoints).
- `API_POLL_FREQUENCY` set in seconds. The number of seconds to wait before polling `FLAGSMITH_API_URL` to update the
  Environments currently in use. Defaults to `10` seconds.
- `WEB_CONCURRENCY` The number of [Uvicorn](https://www.uvicorn.org/) workers. Defaults to `1`. Set to the number of
  available CPU cores.

## Consuming the Edge Proxy

The Edge Proxy provides an identical set of API methods as our Core API. This means you simply need to point your SDK to
the Edge Proxy domain name and you're good to go. For example, lets say you had your proxy running locally as per the
instructions above, you could simply do:

```bash
curl "http://localhost:8000/api/v1/flags" -H "x-environment-key: 95DybY5oJoRNhxPZYLrxk4" | jq

{
  "flags": [
    {
      "id": 78978,
      "feature": {
        "id": 15058,
        "name": "string_feature",
        "created_date": "2021-11-29T17:15:51.694223Z",
        "description": null,
        "initial_value": "foo",
        "default_enabled": true,
        "type": "STANDARD"
      },
      "feature_state_value": "foo",
      "enabled": true,
      "environment": 12561,
      "identity": null,
      "feature_segment": null
    },
    {
      "id": 78980,
      "feature": {
        "id": 15059,
        "name": "integer_feature",
        "created_date": "2021-11-29T17:16:11.288134Z",
        "description": null,
        "initial_value": "1234",
        "default_enabled": true,
        "type": "STANDARD"
      },
      "feature_state_value": 1234,
      "enabled": true,
      "environment": 12561,
      "identity": null,
      "feature_segment": null
    }
  ]
}
```

## Managing Traits

There is one caveat with the Edge Proxy. Because it is entirely stateless, it is not able to persist Trait data into any
sort of datastore. This means that you _have_ to provide the full complement of Traits when requesting the Flags for a
particular Identity. Our SDKs all provide relevant methods to achieve this. An example using `curl` would read as
follows:

```bash
curl -X "POST" "http://localhost:8000/api/v1/identities/?identifier=do_it_all_in_one_go_identity" \
     -H 'X-Environment-Key: n9fbf9h3v4fFgH3U3ngWhb' \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "traits": [
    {
      "trait_value": 123.5,
      "trait_key": "my_trait_key"
    },
    {
      "trait_value": true,
      "trait_key": "my_other_key"
    }
  ],
  "identifier": "do_it_all_in_one_go_identity"
}'
```

Note that the Edge Proxy will currently _not_ send the Trait data back to the Core API.

## Architecture

The standard Flagsmith architecture is very simple:

![Image](/img/edge-proxy-existing.png)

With the proxy added to the mix, things are still simple; they are just lower latency!

![Image](/img/edge-proxy-proxy.png)
