---
title: Edge Proxy
---

The Flagsmith Edge Proxy is a service that you host yourself, that allows you to run an instance of the Flagsmith Engine
close to your servers. If you are running Flagsmith within a server-side environment and you want to have very low
latency flags, you have two options:

1. Run the Edge Proxy within in your own infrastructure and connect to it from your server-side SDKs
2. Run your server-side SDKs in [Local Evaluation Mode](/clients/overview#local-evaluation).

The main benefit to running the Edge Proxy is that you reduce your polling requests against the Flagsmith API itself.

The main benefit to running server side SDKs in [Local Evaluation Mode](/clients/overview#local-evaluation) is that you
get the lowest possible latency.

## How does it work

:::info

The Edge Proxy has the same [caveats as running our SDK in Local Evaluation mode.](/clients/overview#local-evaluation).

:::

You can think of the Edge Proxy as a copy of our Python Server Side SDK, running in
[Local Evaluation Mode](/clients/overview#local-evaluation), with an API interface that is compatible with the Flagsmith
SDK API.

The Edge Proxy runs as a lightweight Docker container. It connects to the Flagsmith API (either powered by us at
api.flagsmith.com or self hosted by you) to get Environment Flags and Segment rules. You can then point the Flagsmith
SDKs to your Edge Proxy; it implements all the current SDK endpoints. This means you can serve a very large number of
requests close to your infrastructure and users, at very low latency. Check out the [architecture below](#architecture).

The Proxy also acts as a local cache, allowing you to make requests to the Proxy without hitting the core API.

## Performance

The Edge Proxy can currently serve ~2,000 requests per second (RPS) at a mean latency of ~7ms on an M1 MacBook Pro with
a simple set of flags. Working with more complex Environments with many Segment rules will bring this RPS number down.

It is stateless and hence close to perfectly scalable being deployed behind a load balancer.

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

## Deployment and Configuration

Please see the [hosting documentation](/deployment/hosting/locally-edge-proxy).

## Architecture

The standard Flagsmith architecture:

![Image](/img/edge-proxy-existing.svg)

With the proxy added to the mix:

![Image](/img/edge-proxy-proxy.svg)
