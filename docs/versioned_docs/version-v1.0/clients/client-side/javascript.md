---
title: Flagsmith Javascript SDK
sidebar_label: Javascript
description: Manage your Feature Flags and Remote Config in your Javascript applications.
slug: /clients/javascript
---

This library can be used with pure Javascript, React (and all other popular frameworks/libraries) and React Native
projects. The source code for the client is available on [Github](https://github.com/flagsmith/flagsmith-js-client).

Example applications for a variety of Javascript frameworks such as React, Vue and Angular, as well as React Native, can
be found here:

- [Flagsmith Framework Examples](https://github.com/flagsmith/flagsmith-js-examples/tree/main)

## Installation

### NPM

```bash
npm i flagsmith --save
```

### NPM for React Native

```bash
npm i react-native-flagsmith --save
```

### Via JavaScript CDN

```html
<script src="https://cdn.jsdelivr.net/npm/flagsmith/index.js"></script>
```

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your environment key in the Environment settings
page.

![Image](/img/api-key.png)

### Example: Initialising the SDK

```javascript
import flagsmith from 'flagsmith or react-native-flagsmith'; //Add this line if you're using flagsmith via npm

flagsmith.init({
 environmentID: '<YOUR_ENVIRONMENT_KEY>',
 // api:"http://localhost:8000/api/v1/" set this if you are self hosting, and point it to your API
 cacheFlags: true, // stores flags in localStorage cache
 enableAnalytics: true, // See https://docs.flagsmith.com/flag-analytics/ for more info
 onChange: (oldFlags, params) => {
  //Occurs whenever flags are changed
  const { isFromServer } = params; //determines if the update came from the server or local cached storage

  //Check for a feature
  if (flagsmith.hasFeature('my_cool_feature')) {
   myCoolFeature();
  }

  //Or, use the value of a feature
  const bannerSize = flagsmith.getValue('banner_size');

  //Check whether value has changed
  const bannerSizeOld = oldFlags['banner_size'] && oldFlags['banner_size'].value;
  if (bannerSize !== bannerSizeOld) {
  }
 },
});
```

## Identifying users

Identifying users allows you to target specific users from the Flagsmith dashboard and configure features and traits.
You can call this before or after you initialise the project, calling it after will re-fetch features from the API.

You can identify the users as part of initialising the client or after with the function `flagsmith.identify`.

User features can be managed by navigating to users on [https://flagsmith.com](https://flagsmith.com) for your desired
project. ![Image](/img/user-features.png)

### Example: Identifying a user after initialising the client

When you initialise the client without an identity, it will fetch the flags for a given environment (unless you provide
`preventFetch:true`).

```javascript
import flagsmith from 'flagsmith';

flagsmith.init({
 environmentID: 'QjgYur4LQTwe5HpvbvhpzK',
 onChange: (oldFlags, params) => {
  //Occurs whenever flags are changed

  const { isFromServer } = params; //determines if the update came from the server or local cached storage

  //Set a trait against the Identity
  flagsmith.setTrait('favourite_colour', 'blue'); //This save the trait against the user, it can be queried with flagsmith.getTrait

  //Check for a feature
  if (flagsmith.hasFeature('my_power_user_feature')) {
   myPowerUserFeature();
  }

  //Check for a trait
  if (!flagsmith.getTrait('accepted_cookie_policy')) {
   showCookiePolicy();
  }

  //Or, use the value of a feature
  const myPowerUserFeature = flagsmith.getValue('my_power_user_feature');

  //Check whether value has changed
  const myPowerUserFeatureOld = oldFlags['my_power_user_feature'] && oldFlags['my_power_user_feature'].value;
  if (myPowerUserFeature !== myPowerUserFeatureOld) {
  }
 },
});

/*
Can be called either after you're done initialising the project or in flagsmith.init with its identity and trait properties 
to prevent flags being fetched twice.
*/
flagsmith.identify('flagsmith_sample_user'); //This will create a user in the dashboard if they don't already exist
```

### Example: Initialising the SDK with a user

Initialising the client with an identity property will retrieve the user's flags instead of the environment defaults.
You can also specify traits at this point which could determine the flags that come back based on segment overrides.

```javascript
import flagsmith from 'flagsmith';

flagsmith.init({
 environmentID: 'QjgYur4LQTwe5HpvbvhpzK',
 identity: 'flagsmith_sample_user',
 traits: { age: 21, country: 'England' }, // these will add to the user's existing traits
 onChange: (oldFlags, params) => {
  //Occurs whenever flags are changed

  const { isFromServer } = params; //determines if the update came from the server or local cached storage

  //Set a trait against the Identity
  flagsmith.setTrait('favourite_colour', 'blue'); //This save the trait against the user, it can be queried with flagsmith.getTrait

  //Check for a feature
  if (flagsmith.hasFeature('my_power_user_feature')) {
   myPowerUserFeature();
  }

  //Check for a trait
  if (!flagsmith.getTrait('accepted_cookie_policy')) {
   showCookiePolicy();
  }

  //Or, use the value of a feature
  const myPowerUserFeature = flagsmith.getValue('my_power_user_feature');

  //Check whether value has changed
  const myPowerUserFeatureOld = oldFlags['my_power_user_feature'] && oldFlags['my_power_user_feature'].value;
  if (myPowerUserFeature !== myPowerUserFeatureOld) {
  }
 },
});
```

## API Reference

See all available types [here](https://github.com/Flagsmith/flagsmith-js-client/blob/main/index.d.ts#L35).

### Initialisation options

| Property                                                         |                                                                                                              Description                                                                                                               | Required |                     Default Value |
| ---------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | -------: | --------------------------------: |
| `environmentID: string`                                          |                                                                     Defines which project environment you wish to get flags for. _example ACME Project - Staging._                                                                     |  **YES** |                              null |
| `onChange?: (previousFlags:IFlags, params:IRetrieveInfo)=> void` |                                     Your callback function for when the flags are retrieved `(previousFlags,{isFromServer:true/false,flagsChanged: true/false, traitsChanged:true/false})=>{...}`                                      |  **YES** |                              null |
| `onError?: (res:{message:string}) => void`                       |                                                                                    Callback function on failure to retrieve flags. `(error)=>{...}`                                                                                    |          |                              null |
| `asyncStorage?:any`                                              | Needed for cacheFlags option, used to tell the library what implementation of AsyncStorage your app uses, i.e. ReactNative.AsyncStorage vs @react-native-community/async-storage, for web this defaults to an internal implementation. |          |                              null |
| `cacheFlags?: boolean`                                           |                                    Any time flags are retrieved they will be cached, flags and identities will then be retrieved from local storage before hitting the API (see cache options) ```                                     |          |                              null |
| `cacheOptions?: {ttl?:number, skipAPI?:boolean}`                 |                                                   A ttl in ms (default to 0 which is infinite) and option to skip hitting the API in flagsmith.init if there's cache available. ```                                                    |          |            {ttl:0, skipAPI:false} |
| `enableAnalytics?: boolean`                                      |                                                               [Enable sending flag analytics](/advanced-use/flag-analytics.md) for getValue and hasFeature evaluations.                                                                |          |                             false |
| `enableLogs?: boolean`                                           |                                                                                                Enables logging for key Flagsmith events                                                                                                |          |                              null |
| `defaultFlags?: IFlags`                                          |                                                                    Allows you define default features, these will all be overridden on first retrieval of features.                                                                    |          |                              null |
| `preventFetch?: boolean`                                         |                                                                                     If you want to disable fetching flags and call getFlags later.                                                                                     |          |                             false |
| `state?: IState`                                                 |                                                                                   Set a predefined state, useful for SSR / isomorphic applications.                                                                                    |          |                             false |
| `api?: string`                                                   |                                                                   Use this property to define where you're getting feature flags from, e.g. if you're self hosting.                                                                    |          | https://api.flagsmith.com/api/v1/ |
| `identity?: string`                                              |                                                                           Specifying an identity will fetch flags for that identity in the initial API call.                                                                           |  **YES** |                              null |
| `traits?:Record<string, string or number or boolean>`            |                                                                           Specifying traits will send the traits for that identity in the initial API call.                                                                            |  **YES** |                              null |

### Available Functions

| Property                                                                                                                                        |                                                                                                                                Description                                                                                                                                |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| <code>init(initialisationOptions)=> Promise&lt;void&gt;</code>                                                                                  |                                                                                                            Initialise the sdk against a particular environment                                                                                                            |
| <code>hasFeature(key:string)=> boolean</code>                                                                                                   |                                                                                       Get the value of a particular feature e.g. `flagsmith.hasFeature("powerUserFeature") // true`                                                                                       |
| <code>getValue<T=string&#124;number&#124;boolean&#124;null>(key:string,{ json?:boolean, fallback?:T })=> string&#124;number&#124;boolean</code> |                                                  Get the value of a particular feature e.g. `flagsmith.getValue("font_size", { fallback: 12 }) // 10`, specifying json:true will automatically parse the value as JSON.                                                   |
| <code>getTrait(key:string)=> string&#124;number&#124;boolean</code>                                                                             |                                                               Once used with an identified user you can get the value of any trait that is set for them e.g. `flagsmith.getTrait("accepted_cookie_policy")`                                                               |
| <code>getState()=>IState</code>                                                                                                                 |                                                                               Retrieves the current state of flagsmith, useful in NextJS / isomorphic applications. `flagsmith.getState()`                                                                                |
| <code>setTrait(key:string, value:string&#124;number&#124;boolean)=> Promise&lt;IFlags&gt;</code>                                                |                                                              Once used with an identified user you can set the value of any trait relevant to them e.g. `flagsmith.setTrait("accepted_cookie_policy", true)`                                                              |
| <code>setTraits(values:Record<string, string&#124;number&#124;boolean>)=> Promise&lt;IFlags&gt;</code>                                          |                                                           Set multiple traits e.g. `flagsmith.setTraits({foo:"bar",numericProp:1,boolProp:true})`. Setting a value of null for a trait will remove that trait.                                                            |
| <code>incrementTrait(key:string, value:number)=> Promise&lt;IFlags&gt;</code>                                                                   |                                                                                You can also increment/decrement a particular trait them e.g. `flagsmith.incrementTrait("click_count", 1)`                                                                                 |
| <code>startListening(ticks=1000:number)=>void</code>                                                                                            |                                                                                                               Poll the api for changes every x milliseconds                                                                                                               |
| <code>stopListening()=>void</code>                                                                                                              |                                                                                                                           Stop polling the api                                                                                                                            |
| <code>getFlags()=> Promise&lt;IFlags&gt;</code>                                                                                                 |                                                         Trigger a manual fetch of the environment features, if a user is identified it will fetch their features. Resolves a promise when the flags are updated.                                                          |
| <code>identify(userId:string, traits?:Record<string, string or number or boolean>)=> Promise&lt;IFlags&gt;</code>                               | Identify as a user, optionally with traits e.g. `{foo:"bar",numericProp:1,boolProp:true}`. This will create a user for your environment in the dashboard if they don't exist, it will also trigger a call to `getFlags()`, resolves a promise when the flags are updated. |
| <code>logout()=>Promise&lt;IFlags&gt;</code>                                                                                                    |                                                                                                   Stop identifying as a user, this will trigger a call to `getFlags()`                                                                                                    |

## Multiple SDK Instances

[Version 1.5 and above](https://github.com/Flagsmith/flagsmith-js-client/releases/tag/1.5.0) allows you to create
multiple instances of the Flagsmith SDK. This may be used when you wish to identify multiple users simultaneously within
your app and retain access to getValue, hasFeature etc for each user.

Type:

```javascript
export function createFlagsmithInstance (): IFlagsmith
```

Usage:

```javascript
import { createFlagsmithInstance } from 'flagsmith';
const flagsmith = createFlagsmithInstance();
const flagsmithB = createFlagsmithInstance();

// now you can use flagsmith as before but in its own instance
```

## FAQs

**How do I call `identify`, `setTraits` etc alongside `init`?**

- `init` should be called once in your application, we recommend you call `init` before any other flagsmith call.
- `init` retrieves flags by default, you can turn this off with the `preventFetch` option to `init`. This is useful for
  when you know you're identifying a user straight after.

**When does onChange callback?**

`onChange` calls when flags are fetched this can be a result of:

- init
- setTrait
- incrementTrait
- getFlags
- identify
- flags evaluated by local storage

Using onChange is best used in combination with your application's state management e.g. onChange triggering an action
to re-evaluate flags with `hasFeature` and `getValue`.

However, if this does not fit in with your development pattern, all the above flagsmith functions return a promise that
resolves when fresh flags have been retrieved.

For example by doing the following:

```javascript
await flagsmith.setTrait('age', 21);
const hasFeature = flagsmith.hasFeature('my_feature');
```

On change calls back with information telling you what has changed, you can use this to prevent any unnecessary
re-renders.

```javascript
onChange(this.oldFlags, {
 isFromServer: true, // flags have come from the server or local storage
 flagsChanged: deepEqualsCheck(oldFlags, newFlags),
 traitsChanged: deepEqualsCheck(oldFlags, newFlags),
});
```

**How does caching flags work?**

If the `cacheFlags` is set to true on `init`, the SDK will cache flag evaluations in local async storage. Upon reloading
the browser, an onChange event will be fired immediately with the local storage flags. The flow for this is as follows

1. `init` is called

2. if `cacheFlags` is enabled, local storage checks for any stored flags and traits.

3. if flags have been found in local storage, `onChange` is triggered with the stored flags.

4. at the same time, fresh flags will be retrieved which will result in another `onChange` callback.

5. whenever flags have been retrieved local storage will be updated.

By default, these flags will be persisted indefinitely, you can clear this by removing `"BULLET_TRAIN_DB"` from
`localStorage`.
