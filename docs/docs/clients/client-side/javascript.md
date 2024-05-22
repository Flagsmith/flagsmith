---
title: Flagsmith JavaScript SDK
sidebar_label: JavaScript
description: Manage your Feature Flags and Remote Config in your JavaScript applications.
slug: /clients/javascript
---

This library can be used with pure JavaScript, React (and all other popular frameworks/libraries) and React Native
projects. The source code for the client is available on [GitHub](https://github.com/flagsmith/flagsmith-js-client).

Example applications for a variety of JavaScript frameworks such as React, Vue and Angular, as well as React Native, can
be found here:

- [Flagsmith Framework Examples](https://github.com/Flagsmith/flagsmith-js-examples/tree/main)

## Installation

### NPM

:::tip

We also have flagsmith-es if you'd prefer to use [ES](https://262.ecma-international.org/6.0/) modules.

:::

```bash
npm i flagsmith --save
```

### NPM for React Native

:::tip

The React Native SDK shares the exact same implementation of Flagsmith, however it requires an implementation of
AsyncStorage to be provided (e.g. @react-native-community/async-storage) in order to utilise analytics and caching. See
[here](/clients/javascript#initialisation-options).

:::

```bash
npm i react-native-flagsmith --save
```

### Via JavaScript CDN

```html
<script src="https://cdn.jsdelivr.net/npm/flagsmith/index.js"></script>
```

## Basic Usage

The SDK is initialised against a single environment within a project on [https://flagsmith.com](https://flagsmith.com),
for example the Development or Production environment. You can find your Client-side Environment Key in the Environment
settings page.

### Example: Initialising the SDK

```javascript
import flagsmith from 'flagsmith or react-native-flagsmith'; //Add this line if you're using flagsmith via npm

flagsmith.init({
 environmentID: '<YOUR_CLIENT_SIDE_ENVIRONMENT_KEY>',
 // api:"http://localhost:8000/api/v1/" set this if you are self hosting, and point it to your API
 cacheFlags: true, // stores flags in localStorage cache
 enableAnalytics: true, // See https://docs.flagsmith.com/flag-analytics/ for more info.
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
   // Do something!
  }
 },
});
```

:::info

As of flagsmith 4.0.0, `flagsmith.init` will return a promise resolving with either cache or the latest features or
defaults. The promise will reject if there is no cache and an invalid or no API response was received.

:::

### Providing Default Flags

You can define default flag values when initialising the SDK. This ensures that your application works as intended in
the event that it [cannot receive a response from our API](/guides-and-examples/defensive-coding).

```javascript
import flagsmith from 'flagsmith or react-native-flagsmith'; //Add this line if you're using flagsmith via npm

flagsmith.init({
    environmentID: '<YOUR_CLIENT_SIDE_ENVIRONMENT_KEY>',
    defaultFlags: {
        feature_a: { enabled: false},
        font_size: { enabled: true, value: 12 },
    }
    onChange: (oldFlags, params) => {
        ...
    },
});
```

### Providing Default Flags as part of CI/CD

You can automatically set default flags for your frontend application in CI/CD by using our
[CLI](https://github.com/Flagsmith/flagsmith-cli) in your build pipelines.

The main steps to achieving this are as follows:

1. Install the CLI `npm i flagsmith-cli --save-dev`
2. Call the CLI as part of npm postinstall to create a `flagsmith.json` each time you run `npm install`. This can be
   done by either:

   - Using an environment variable `export FLAGSMITH_ENVIRONMENT=<YOUR_CLIENT_SIDE_ENVIRONMENT_KEY> flagsmith get`
   - Manually specifying your environment key `flagsmith get <YOUR_CLIENT_SIDE_ENVIRONMENT_KEY>`.

3. In your application, initialise Flagsmith with the resulting JSON, this will set default flags before attempting to
   use local storage or call the API. `flagsmith.init({environmentID: json.environmentID, state:json})`

A working example of this can be found [here](https://github.com/Flagsmith/flagsmith-cli/tree/main/example). A list of
cli commands can be found [here](https://github.com/Flagsmith/flagsmith-cli).

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
 environmentID: '<YOUR_CLIENT_SIDE_ENVIRONMENT_KEY>',
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
   // Do something!
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
 environmentID: '<YOUR_CLIENT_SIDE_ENVIRONMENT_KEY>',
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

All function and property types can be seen
[here](https://github.com/Flagsmith/flagsmith-js-client/blob/main/types.d.ts#L35).

### Initialisation options

| Property                                                                                    |                                                                                                                    Description                                                                                                                    | Required |                                         Default Value |
| ------------------------------------------------------------------------------------------- | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | -------: | ----------------------------------------------------: |
| `environmentID: string`                                                                     |                                                                          Defines which project environment you wish to get flags for. _example ACME Project - Staging._                                                                           |  **YES** |                                                  null |
| `onChange?: (previousFlags:IFlags, params:IRetrieveInfo, loadingState:LoadingState)=> void` |                                           Your callback function for when the flags are retrieved `(previousFlags,{isFromServer:true/false,flagsChanged: true/false, traitsChanged:true/false})=>{...}`                                           |  **YES** |                                                  null |
| `onError?: (res:{message:string}) => void`                                                  |                                                                                         Callback function on failure to retrieve flags. `(error)=>{...}`                                                                                          |          |                                                  null |
| `realtime?:boolean`                                                                         |                                                                                   Whether to listen for [Real Time Flag events](/advanced-use/real-time-flags)                                                                                    |          |                                                 false |
| `AsyncStorage?:any`                                                                         | Needed in certain frameworks cacheFlags and enableAnalytics options, used to tell the library what implementation of AsyncStorage your app uses, e.g. @react-native-community/async-storage, for web this defaults to an internal implementation. |          | built in implementation for web, otherwise undefined. |
| `cacheFlags?: boolean`                                                                      |                       Any time flags are retrieved they will be cached, flags and identities will then be retrieved from local storage before hitting the API (see cache options). Requires AsyncStorage to be accessible.                        |          |                                                  null |
| `cacheOptions?: \{ttl?:number, skipAPI?:boolean\}`                                          |                                                           A ttl in ms (default to 0 which is infinite) and option to skip hitting the API in flagsmith.init if there's cache available.                                                           |          |                              \{ttl:0, skipAPI:false\} |
| `enableAnalytics?: boolean`                                                                 |                                                                     [Enable sending flag analytics](/advanced-use/flag-analytics.md) for getValue and hasFeature evaluations.                                                                     |          |                                                 false |
| `enableLogs?: boolean`                                                                      |                                                                                                     Enables logging for key Flagsmith events                                                                                                      |          |                                                  null |
| `defaultFlags?: {flag_name: {enabled: boolean, value: string,number,boolean}}`              |                                                                         Allows you define default features, these will all be overridden on first retrieval of features.                                                                          |          |                                                  null |
| `preventFetch?: boolean`                                                                    |                                                                                          If you want to disable fetching flags and call getFlags later.                                                                                           |          |                                                 false |
| `state?: IState`                                                                            |                                                                                         Set a predefined state, useful for SSR / isomorphic applications.                                                                                         |          |                                                 false |
| `api?: string`                                                                              |                                                                         Use this property to define where you're getting feature flags from, e.g. if you're self hosting.                                                                         |          |                https://edge.api.flagsmith.com/api/v1/ |
| `eventSourceUrl?: string`                                                                   |                                                       Use this property to define where you're getting real-time flag update events (server sent events) from, e.g. if you're self hosting.                                                       |          |                https://edge.api.flagsmith.com/api/v1/ |
| `identity?: string`                                                                         |                                                                                Specifying an identity will fetch flags for that identity in the initial API call.                                                                                 |  **YES** |                                                  null |
| `traits?:Record<string, string or number or boolean>`                                       |                                                                                 Specifying traits will send the traits for that identity in the initial API call.                                                                                 |  **YES** |                                                  null |

### Available Functions

| Property                                                                                                                                            |                                                                                                                                Description                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| <code>init(initialisationOptions)=> Promise&lt;void&gt;</code>                                                                                      |                                                                                                            Initialise the sdk against a particular environment                                                                                                            |
| <code>hasFeature(key:string)=> boolean</code>                                                                                                       |                                                                                       Get the value of a particular feature e.g. `flagsmith.hasFeature("powerUserFeature") // true`                                                                                       |
| <code>getValue\<T=string&#124;number&#124;boolean&#124;null\>(key:string,\{ json?:boolean, fallback?:T \})=> string&#124;number&#124;boolean</code> |                                                  Get the value of a particular feature e.g. `flagsmith.getValue("font_size", { fallback: 12 }) // 10`, specifying json:true will automatically parse the value as JSON.                                                   |
| <code>getTrait(key:string)=> string&#124;number&#124;boolean</code>                                                                                 |                                                               Once used with an identified user you can get the value of any trait that is set for them e.g. `flagsmith.getTrait("accepted_cookie_policy")`                                                               |
| <code>getAllTraits()=> Record&lt;string,string&#124;number&#124;boolean&gt;</code>                                                                  |                                                                      Once used with an identified user you can get a key value pair of all traits that are set for them e.g. `flagsmith.getTraits()`                                                                      |
| <code>getState()=>IState</code>                                                                                                                     |                                                                               Retrieves the current state of flagsmith, useful in NextJS / isomorphic applications. `flagsmith.getState()`                                                                                |
| <code>setState(state: IState)=>void</code>                                                                                                          |                              Set the current state of flagsmith, [useful in NextJS / isomorphic applications.](/clients/next-ssr#comparing-ssr-and-client-side-flagsmith-usage) e.g. `flagsmith.setState({identity: 'mary@mycompany.com'})`.                              |
| <code>setTrait(key:string, value:string&#124;number&#124;boolean)=> Promise&lt;IFlags&gt;</code>                                                    |                                                              Once used with an identified user you can set the value of any trait relevant to them e.g. `flagsmith.setTrait("accepted_cookie_policy", true)`                                                              |
| <code>setTraits(values:Record\<string, string&#124;number&#124;boolean>)=\> Promise&lt;IFlags&gt;</code>                                            |                                                           Set multiple traits e.g. `flagsmith.setTraits({foo:"bar",numericProp:1,boolProp:true})`. Setting a value of null for a trait will remove that trait.                                                            |
| <code>incrementTrait(key:string, value:number)=> Promise&lt;IFlags&gt;</code>                                                                       |                                                                                You can also increment/decrement a particular trait them e.g. `flagsmith.incrementTrait("click_count", 1)`                                                                                 |
| <code>startListening(ticks=1000:number)=>void</code>                                                                                                |                                                                                                               Poll the api for changes every x milliseconds                                                                                                               |
| <code>stopListening()=>void</code>                                                                                                                  |                                                                                                                           Stop polling the api                                                                                                                            |
| <code>getFlags()=> Promise&lt;IFlags&gt;</code>                                                                                                     |                                                         Trigger a manual fetch of the environment features, if a user is identified it will fetch their features. Resolves a promise when the flags are updated.                                                          |
| <code>getAllFlags()=> &lt;IFlags&gt;</code>                                                                                                         |                                                                                                                        Returns the current flags.                                                                                                                         |
| <code>identify(userId:string, traits?:Record\<string, string or number or boolean\>)=> Promise&lt;IFlags&gt;</code>                                 | Identify as a user, optionally with traits e.g. `{foo:"bar",numericProp:1,boolProp:true}`. This will create a user for your environment in the dashboard if they don't exist, it will also trigger a call to `getFlags()`, resolves a promise when the flags are updated. |
| <code>logout()=>Promise&lt;IFlags&gt;</code>                                                                                                        |                                                                                                   Stop identifying as a user, this will trigger a call to `getFlags()`                                                                                                    |

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

## Flagsmith Loading State

[Version 3.19 and above](https://github.com/Flagsmith/flagsmith-js-client/releases/tag/3.19.0) allows you to determine
the current loading state of the SDK and whether its current data is from default flags, cache or the API. Flagsmith
loading state can be accessed via the onChange event and the
[`useFlagsmithLoading()`](react#useflagsmithloading-api-reference) hook in the React SDK. The expected type of Flagsmith
loading state is as follows:

```typescript
export declare enum FlagSource {
 'NONE' = 'NONE',
 'DEFAULT_FLAGS' = 'DEFAULT_FLAGS',
 'CACHE' = 'CACHE',
 'SERVER' = 'SERVER',
}

export declare type LoadingState = {
 error: Error | null; // Current error, resets on next attempt to fetch flags
 isFetching: bool; // Whether there is a current request to fetch server flags
 isLoading: bool; // Whether any flag data exists
 source: FlagSource; //Indicates freshness of flags
};
```

## JSON Feature Values

The Flagsmith JavaScript client supports JSON remote config / feature values. When calling `flagsmith.getValue`,
specifying `json:true` will attempt to parse the feature value as JSON, it will fallback to `fallback` failing to parse
it.

```javascript
const json = flagsmith.getValue('json_value', {
 json: true,
 fallback: { foo: null, bar: null },
});
```

## TypeScript Support

Flagsmith has full TypeScript support for its JavaScript clients, you can find our main type definition file
[here](https://github.com/Flagsmith/flagsmith-js-client/blob/main/types.d.ts#L35). You can also enforce type safety of
feature and trait names using generics:

Given that we type our flags and traits:

```typescript
type FlagOptions = 'font_size' | 'hero';
type TraitOptions = 'example_trait';
```

We can now enforce these types:

```typescript
// enforces you passing the correct key to flagsmith.getValue(flag:FlagOptions), flagsmith.getTrait(trait:TraitOptions)
import flagsmith from 'flagsmith';
const typedFlagsmith = flagsmith as IFlagsmith<FlagOptions, TraitOptions>;

// Similarly for the useFlagsmith hook is typed with useFlagsmith(flags:FlagOptions[],traits:TraitOptions[])
const flagsmith = useFlagsmith<FlagOptions, TraitOptions>(); // enforces flagsmith.getValue()

// for useFlags this will ensure you only can pass correct keys also
const flags = useFlags<FlagOptions, TraitOptions>(['font_size'], ['example_trait']);

// for getting JSON values this will type the return
const json = flagsmith.getValue<{ foo: string | null; bar: string | null }>('json_value', {
 json: true,
 fallback: { foo: null, bar: null },
});
console.log(json.foo); // typed as {foo: string|null, bar: string|null}

// If a type is not specified for getValue it will asume it from the type of fallback. In this case, a number.
const font_size = flagsmith.getValue('font_size', { fallback: 12 });
```

## Datadog RUM JavaScript SDK Integration

:::caution

This feature is still in beta with Datadog. Contact your Datadog representative before enabling the integration below.

:::

The Flagsmith JavaScript SDK can be configured so that feature enabled state and remote config can be stored as
[Datadog RUM feature flags](https://docs.datadoghq.com/real_user_monitoring/guide/setup-feature-flag-data-collection/?tab=npm#analyze-your-feature-flag-performance-in-rum)
and user traits can be stored as
[Datadog user session properties](https://docs.datadoghq.com/real_user_monitoring/browser/modifying_data_and_context/?tab=npm#addoverride-user-session-property).
The integration requires an initialised Datadog `datadogRum` client.

### Step 1: Initialise your Datadog RUM SDK with the feature_flags experimental feature

To start collecting feature flag data, initialize the Datadog RUM SDK and configure the enableExperimentalFeatures
initialization parameter with ["feature_flags"].

```typescript
import { datadogRum } from '@datadog/browser-rum';

// Initialize Datadog Browser SDK
datadogRum.init({
    enableExperimentalFeatures: ["feature_flags"],
    ...
});
```

### Step 2: Initialise the Flagsmith SDK with configuring

Initialise the Flagsmith SDK with the datadogRum option. Optionally, you can configure the client so that Flagsmith
traits are sent to Datadog via ``datadogRum.setUser()````.

```typescript
import { datadogRum } from '@datadog/browser-rum';
...
// Initialize the Flagsmith SDK
flagsmith.init({
    datadogRum: {
        client: datadogRum,
        trackTraits: true,
    },
    ...
})
```

### Step 3: What happens next

- Whenever flag values are _evaluated_ in your code, they will be sent to Datadog as user events.
- If the option to send Traits is enabled, the Trait key/value pairs will be sent to Datadog when the SDK receives its
  Flags.

This will track remote config and feature enabled states as feature flags in the following format

```bash
flagsmith_value_<FEATURE_NAME> // remote config
flagsmith_enabled_<FEATURE_NAME> // enabled state
```

Additionally, the integration will also store Flagsmith traits against the Datadog user in the following format:

```bash
flagsmith_trait_<FEATURE_NAME> // remote config
```

You can find an example of this integration
[here](https://github.com/Flagsmith/flagsmith-js-examples/blob/main/datadog-realtime-user-monitoring/src/index.tsx).

## Dynatrace JavaScript SDK Integration

The Flagsmith JavaScript SDK can be configured so that feature enabled state, remote config and user traits can be
stored as Dynatrace session properties. The integration requires a configured Dynatrace `dtrum` object that is already
set up.

### Step 1: Pass `enableDynatrace` into `flagsmith.init()`

In order to configure the JavaScript SDK, you need to pass in an instance of
[dtrum](https://www.dynatrace.com/support/help/how-to-use-dynatrace/real-user-monitoring/basic-concepts/js-tag-api).

```javascript
// Initialize the Flagsmith SDK
flagsmith.init({
 //...Initialisation properties,
 enableDynatrace: true,
});
```

When setting `enableDynatrace` to true `flagsmith.init`, Flagsmith will send session properties corresponding to flag
enabled state, flag values and user traits via
[dtrum.sendSessionProperties()](https://www.dynatrace.com/support/doc/javascriptapi/interfaces/dtrum_types.DtrumApi.html#sendSessionProperties)

- flag enabled state sends as a **shortString** as `true` or `false` with the prefix `flagsmith_enabled_`
  - example: `flagsmith_enabled_hero: "true"`
- Remote config values sends as value with the prefix flagsmith _value_, this value will be a **javaDouble** for numeric
  values and a **shortString** for any other.
  - example: `flagsmith_value_font_size: 21`, `flagsmith_value_hero_colour: "blue"`
- Remote config values sends as value with the prefix flagsmith _value_, this value will be a **javaDouble** for numeric
  values and a **shortString** for any other.
  - example: `flagsmith_trait_age: 21`, `flagsmith_trait_favourite_colour: "blue"`

### Step 2: Add the session properties to your Dynatrace application settings

[As with any other Dynatrace session properties](https://www.dynatrace.com/support/help/how-to-use-dynatrace/real-user-monitoring/setup-and-configuration/web-applications/additional-configuration/define-user-action-and-session-properties),
you need to also define session properties within the RUM application settings.

You can also add these properties via the
[Dynatrace API](https://www.dynatrace.com/support/help/dynatrace-api/configuration-api/rum/mobile-custom-app-configuration/user-action-and-session-properties/post-property).

### Dynatrace Screenshots

Defining Dynatrace Properties:

![Image](/img/dynatrace_1.png)

Defining a Flagsmith and Dynatrace Property:

![Image](/img/dynatrace_2.png)

Filtering on a Flagsmith Flag:

![Image](/img/dynatrace_3.png)

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
onChange(oldFlags, {
 isFromServer: true, // flags have come from the server or local storage
 flagsChanged: string[] | null,
 traitsChanged: string[] | null,
}, loadingState)
```

:::info

Prior to `flagsmith 4.0.0`, flagsChanged and traitsChanged returned a boolean.

:::

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

**Why am I seeing `ReferenceError: XMLHttpRequest is not defined`?**

The Flagsmith JavaScript client uses the [fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
API to handle REST calls. Some frameworks such as Manifest and Nuxt do not support this out of the box.

In order to resolve this issue, you can provide a custom fetch implementation to the Flagsmith SDK. An example of this
can be found [here](https://github.com/Flagsmith/flagsmith-js-examples/blob/main/nuxt/plugins/flagsmith-plugin.ts#L9).
