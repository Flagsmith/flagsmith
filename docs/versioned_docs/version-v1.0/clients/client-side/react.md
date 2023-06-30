---
title: Flagsmith React SDK
sidebar_label: React and React Native
description: Manage your Feature Flags and Remote Config with React and React Native Hooks.
slug: /clients/react
---

This library includes React/React Native Hooks allowing you to query individual features and flags that limit
re-renders.

Example applications for a variety of React, React Native and Next.js can be found here:

- [Usage with React](https://github.com/Flagsmith/flagsmith-js-examples/tree/main/react)
- [Usage with React Native](https://github.com/Flagsmith/flagsmith-js-examples/tree/main/react)
- [Usage with Next.js](https://github.com/Flagsmith/flagsmith-js-examples/tree/main/nextjs)

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
for example, the Development or Production environment. ![Image](/img/api-key.png)

### Step 1: Wrapping your application with Flagsmith Provider

Wrapping your application with our FlagsmithProvider component provides a React Context throughout your application so
that you can use the hooks `useFlagsmith` and `useFlags`.

```javascript
import flagsmith from 'flagsmith'
import {FlagsmithProvider} from 'flagsmith/react'

export function AppRoot() {
  <FlagsmithProvider options={{
      environmentID: "<YOUR_ENVIRONMENT_KEY>",
  }} flagsmith={flagsmith}>
    {...}
  </FlagsmithProvider>
);
```

Providing options to the Flagsmith provider will initialise the client, the API reference for these options can be found
[here](/clients/javascript#initialisation-options).

**Advanced usage: Initialising before rendering the FlagsmithProvider**

If you wish to initialise the Flagsmith client before React rendering (e.g. in redux, or SSR) you can do so by calling
[flagsmith.init](https://docs.flagsmith.com/clients/javascript#example-initialising-the-sdk) and provide no options
property to the FlagsmithProvider component.

### Step 2: Using useFlags to access feature values and enabled state

Components that have been wrapped in a FlagsmithProvider will be able to evaluate feature values and enabled state as
well as user traits via the `useFlags` hook.

```javascript
import { useFlags } from 'flagsmith/react';

export function MyComponent() {
 const flags = useFlags(['font_size'], ['example_trait']); // only causes re-render if specified flag values / traits change
 return (
  <div className="App">
   font_size: {flags.font_size.value}
   example_trait: {flags.example_trait}
  </div>
 );
}
```

## useFlags API Reference

```javascript
useFlags(requiredFlags:string[], requiredTraits?:string[])=> {[key:string]: IFlagsmithTrait  or IFlagsmithFeature}
```

## FlagsmithProvider API Reference

| Property                 |                                                  Description                                                   | Required | Default Value |
| ------------------------ | :------------------------------------------------------------------------------------------------------------: | -------: | ------------: |
| `flagsmith: IFlagsmith`  |                           Defines the flagsmith instance that the provider will use.                           |  **YES** |          null |
| `options?: ` IInitConfig |    Initialisation options to use. If you don't provide this you will have to call flagsmith.init elsewhere.    |          |          null |
| `serverState?: IState`   | Used to pass an initial state, in most cases as a result of SSR flagsmith.getState(). See [Next.js and SSR](/) |          |          null |

### Step 3: Using useFlagsmith to access the Flagsmith instance

Components that have been wrapped in a FlagsmithProvider will be able to access the instance of Flagsmith via the
`useFlagsmith` hook.

```javascript
import React from 'react';
import { useFlags, useFlagsmith } from 'flagsmith/react';

export function MyComponent() {
 const flags = useFlags(['font_size'], ['example_trait']); // only causes re-render if specified flag values / traits change
 const flagsmith = useFlagsmith();
 const identify = () => {
  // This will re-render the component if the user has the trait example_trait or they have a different feature value for font_size
  flagsmith.identify('flagsmith_sample_user');
 };
 const logout = () => {
  // This will re-render the component if the user has the trait example_trait or they have a different feature value for font_size
  flagsmith.logout();
 };
 return (
  <div className="App">
   font_size: {flags.font_size?.value}
   example_trait: {flags.example_trait}
   {flagsmith.identity ? <button onClick={logout}>Logout</button> : <button onClick={identify}>Identify</button>}
  </div>
 );
}
```

## useFlagsmith API Reference

```javascript
useFlagsmith()=> IFlagsmith
```
