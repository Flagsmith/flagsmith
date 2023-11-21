---
title: Flagsmith React SDK
sidebar_label: Next.js and SSR
description: Manage your Feature Flags and Remote Config with NextJS and SSR.
slug: /clients/next-ssr
---

The JavaScript Library contains a bundled isomorphic library, allowing you to fetch flags in the server and hydrate your
application with the resulting state.

Example applications for a variety of Next.js and SSR can be found
[here](https://github.com/flagsmith/flagsmith-js-examples/tree/main/nextjs).

Example applications for Svelte be found [here](https://github.com/flagsmith/flagsmith-js-examples/tree/main/svelte).

An example application for Next.js middleware can be found
[here](https://github.com/flagsmith/flagsmith-js-examples/tree/main/nextjs-middleware).

## Installation

### NPM

```bash
npm i flagsmith --save
```

## Basic Usage

The SDK is initialised against a single environment. You can find your Client-side Environment Key in the Environment
settings page.

## Comparing SSR and client-side Flagsmith usage

The SDK is initialised and used in the same way as the [JavaScript](/clients/javascript) and [React](/clients/react)
SDK. The main difference is that Flagsmith should be imported from `flagsmith/isomorphic`.

The main flow with Next.js and any JavaScript-based SSR can be as follows:

1. Fetch the flags on the server, optionally passing an identity to
   [`flagsmith.init({})`](/clients/javascript#initialisation-options)
2. Pass the resulting state to the client with [`flagsmith.getState()`](/clients/javascript#available-functions)
3. Initialise flagsmith on the client with [`flagsmith.setState(state)`](/clients/javascript#available-functions)

### Example: Initialising the SDK with Next.js

Taking the above into account, the following example fetches flags on the server and initialises Flagsmith with the
state.

```javascript
import { FlagsmithProvider } from 'flagsmith/react';
import { createFlagsmithInstance } from 'flagsmith/isomorphic';
function MyApp({ Component, pageProps, flagsmithState }) {
 const flagsmithRef = useRef(createFlagsmithInstance());
 return (
  <FlagsmithProvider flagsmith={flagsmithRef.current} serverState={flagsmithState}>
   <Component {...pageProps} />
  </FlagsmithProvider>
 );
}

MyApp.getInitialProps = async () => {
 const flagsmithSSR = createFlagsmithInstance();
 await flagsmithSSR.init({
  // fetches flags on the server
  environmentID: '<YOUR_ENVIRONMENT_ID>',
  identity: 'my_user_id', // optionaly specify the identity of the user to get their specific flags
 });
 return { flagsmithState: flagsmithSSR.getState() };
};

export default MyApp;
```

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

From that point the SDK usage is the same as the [React SDK Guide](/clients/react)

### Example: Flagsmith with Next.js middleware

The Flagsmith JS client includes `flagsmith/next-middleware`, it can be used just like the regular library within
Next.js middleware.

```javascript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import flagsmith from 'flagsmith/next-middleware';

export async function middleware(request: NextRequest) {
 const identity = request.cookies.get('user');

 if (!identity) {
  // redirect to homepage
  return NextResponse.redirect(new URL('/', request.url));
 }

 await flagsmith.init({
  environmentID: '<YOUR_ENVIRONMENT_ID>',
  identity,
 });

 // Return a different URL based on a feature flag
 if (flagsmith.hasFeature('beta')) {
  return NextResponse.redirect(new URL(`/account-v2/`, request.url));
 }

 // Return a different URL based on a remote config
 const theme = flagsmith.getValue('colour');
 return NextResponse.redirect(new URL(`/account/${theme}`, request.url));
}

export const config = {
 matcher: '/login',
};
```

### Example: SSR without Next.js

The same can be accomplished without using Next.js.

Step 1: Initialising the SDK and passing the resulting state to the client.

```javascript
await flagsmith.init({
 // fetches flags on the server
 environmentID: '<YOUR_ENVIRONMENT_ID>',
 identity: 'my_user_id', // optionaly specify the identity of the user to get their specific flags
});
const state = flagsmith.getState(); // Pass this data to your client
```

Step 2: Initialising the SDK on the client.

```javascript
flagsmith.setState(state); // set the state based on your
```

Step 3: Optionally force the client to fetch a fresh set of flags

```javascript
flagsmith.getFlags(); // set the state based on your
```

From that point the SDK usage is the same as the [JavaScript SDK Guide](/clients/javascript)
