---
title: "Caching Strategies"
description: "How to configure caching for API endpoints and the environment document."
sidebar_position: 40
---

The application utilises an in-memory cache for a number of different API endpoints to improve performance. The main things that are cached are listed below:

1. Environment flags - the application utilises an in memory cache for the flags returned when calling /flags. The number of seconds this is cached for is configurable using the environment variable `"CACHE_FLAGS_SECONDS"`
2. Project segments - the application utilises an in memory cache for returning the segments for a given project. The number of seconds this is cached for is configurable using the environment variable `"CACHE_PROJECT_SEGMENTS_SECONDS"`.
3. Flags and identities endpoint caching - the application provides the ability to cache the responses to the GET /flags and GET /identities endpoints. The application exposes the configuration to allow the caching to be handled in a manner chosen by the developer. The configuration options are explained in more detail below.
4. Environment document - when making heavy use of the environment document, it is often wise to utilise caching to reduce the load on the database. Details are provided below.

## Flags & Identities Endpoint Caching

To enable caching on the flags and identities endpoints (GET requests only), you must set the following environment variables:

| Environment Variable                                               | Description                                                                                                                    | Example value                                          | Default                                       |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ | --------------------------------------------- |
| `FLAG_IDENTITY_CACHE_LOCATION`                                     | The location to cache the flags and identities endpoints. One of `default` or `redis`.                                         | `redis`                                                |                                               |
| `FLAG_IDENTITY_CACHE_TTL_SECONDS`                                  | The number of seconds to cache the flags and identities endpoints for.                                                         | `60`                                                   | `0` (i.e. don't cache)                        |

## Environment Document Caching

To enable caching on the environment document endpoint, you must set the following environment variables:

:::caution

Persistent cache should only be used with cache backends that offer a centralised cache. It should not be used with e.g. LocMemCache.

:::

:::info

When using a persistent cache, a change can take a few seconds to update the cache. This can also be optimised by increasing the performance of your task processor.

:::

| Environment Variable                  | Description                                                                                                                                                                                       | Example value                                          | Default                                       |
|---------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------|-----------------------------------------------|
| `CACHE_ENVIRONMENT_DOCUMENT_MODE`     | The caching mode. One of `PERSISTENT` or `EXPIRING`. Note that although the default is `EXPIRING` there is no caching by default due to the default value of `CACHE_ENVIRONMENT_DOCUMENT_SECONDS` | `PERSISTENT`                                           | `EXPIRING`                                    |
| `CACHE_ENVIRONMENT_DOCUMENT_SECONDS`  | Number of seconds to cache the environment for (only relevant when `CACHE_ENVIRONMENT_DOCUMENT_MODE=EXPIRING`)                                                                                    | `60`                                                   | `0` ( = don't cache)                          | 