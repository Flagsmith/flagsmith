---
title: Flagsmith NodeJS SDK
sidebar_label: NodeJS
description: Manage your Feature Flags and Remote Config in your NodeJS applications.
slug: /clients/node
---

This library can be used with server-side NodeJS projects. The source code for the client is available on
[Github](https://github.com/flagsmith/flagsmith-nodejs-client).

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing
purposes. See running in production for notes on how to deploy the project on a live system.

## Installing

VIA npm:

`npm i flagsmith-nodejs --save`

## Usage

### Retrieving feature flags for your project

```javascript
const flagsmith = require('flagsmith-nodejs');

flagsmith.init({
 environmentID: '<YOUR_ENVIRONMENT_KEY>',
});

flagsmith.hasFeature('header', '<My User Id>').then((featureEnabled) => {
 if (featureEnabled) {
  //Show my awesome cool new feature to this one user
 }
});

flagsmith.hasFeature('header').then((featureEnabled) => {
 if (featureEnabled) {
  //Show my awesome cool new feature to the world
 }
});

flagsmith.getValue('header', '<My User Id').then((value) => {
 //Show some unique value to this user
});

flagsmith.getValue('header').then((value) => {
 //Show a value to the world
});
```

## Available Options

| Property        |                                            Description                                            | Required |                      Default Value |
| --------------- | :-----------------------------------------------------------------------------------------------: | -------: | ---------------------------------: |
| `environmentID` |  Defines which project environment you wish to get flags for. _example ACME Project - Staging._   |  **YES** |                               null |
| `onError`       |                 Callback function on failure to retrieve flags. `(error)=>{...}`                  |   **NO** |                               null |
| `api`           | Use this property to define where you're getting feature flags from, e.g. if you're self hosting. |   **NO** | <https://api.flagsmith.com/api/v1> |
| `cache`         |  Defines an object containing 3 functions (`has(k)`, `get(k)`, `set(k,v)`) to cache API results   |   **NO** |                               null |

## Available Functions

| Property                       |                                                  Description                                                   |
| ------------------------------ | :------------------------------------------------------------------------------------------------------------: |
| `init`                         |                              Initialise the sdk against a particular environment                               |
| `hasFeature(key)`              |         Get the value of a particular feature e.g. `flagsmith.hasFeature("powerUserFeature") // true`          |
| `hasFeature(key, userId)`      | Get the value of a particular feature for a user e.g. `flagsmith.hasFeature("powerUserFeature", 1234) // true` |
| `getValue(key)`                |               Get the value of a particular feature e.g. `flagsmith.getValue("font_size") // 10`               |
| `getValue(key, userId)`        | Get the value of a particular feature for a specificed user e.g. `flagsmith.getValue("font_size", 1234) // 15` |
| `getFlags()`                   |                               Trigger a manual fetch of the environment features                               |
| `getFlagsForUser(userId)`      |                     Trigger a manual fetch of the environment features for a given user id                     |
| `getUserIdentity(userId)`      |         Trigger a manual fetch of both the environment features and users' traits for a given user id          |
| `getTrait(userId, key)`        |                         Trigger a manual fetch of a specific trait for a given user id                         |
| `setTrait(userId, key, value)` |                                    Set a specific trait for a given user id                                    |

## Identifying users

Identifying users allows you to target specific users from the [Flagsmith dashboard](https://www.flagsmith.com/). You
can include an optional user identifier as part of the `hasFeature` and `getValue` methods to retrieve unique user flags
and variables.

## Caching Data

You can initialise the SDK with something like this:

```javascript
flagsmith.init({
 cache: {
   has:(key)=> return Promise.resolve(!!cache[key]) , // true | false
   get: (k)=> cache[k] // return flags or flags for user
   set: (k,v)=> cache[k] = v // gets called if has returns false with response from API for Identify or getFlags
  }
})
```

The core concept is that if `has` returns false, the SDK will make the required API calls under the hood. The keys are
either `flags` or `flags_traits-${identity}`.

An example of a concrete implemention is below.

```javascript
const flagsmith = require('flagsmith-nodejs');
const redis = require('redis');

const redisClient = redis.createClient({
 host: 'localhost',
 port: 6379,
});

flagsmith.init({
 environmentID: '<Flagsmith Environment API Key>',
 cache: {
  has: (key) =>
   new Promise((resolve, reject) => {
    redisClient.exists(key, (err, reply) => {
     console.log('check ' + key + ' from cache', err, reply);
     resolve(reply === 1);
    });
   }),
  get: (key) =>
   new Promise((resolve) => {
    redisClient.get(key, (err, cacheValue) => {
     console.log('get ' + key + ' from cache');
     resolve(cacheValue && JSON.parse(cacheValue));
    });
   }),
  set: (key, value) =>
   new Promise((resolve) => {
    // Expire the key after 60 seconds
    redisClient.set(key, JSON.stringify(value), 'EX', 60, (err, reply) => {
     console.log('set ' + key + ' to cache', err);
     resolve();
    });
   }),
 },
});

router.get('/', function (req, res, next) {
 flagsmith.getValue('background_colour').then((value) => {
  res.render('index', {
   title: value,
  });
 });
});
```
