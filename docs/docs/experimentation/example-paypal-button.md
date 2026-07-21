---
title: 'Example: Testing a PayPal Button'
sidebar_label: 'Example: PayPal Button'
sidebar_position: 8
description: An end-to-end walkthrough of a real experiment, from flag to rollout.
---

:::info Enterprise beta

Experimentation is in beta on **Enterprise** plans. [Get in touch](https://www.flagsmith.com/contact-us) to join.

:::

Our app currently accepts credit card payments only. We suspect offering PayPal will increase completed checkouts, and
we want to prove it on a small slice of traffic before rolling it out. This page walks through the whole experiment.

## 1. Create the flag

Create a [multivariate flag](/managing-flags/core-management) called `paypal_button`. The flag's current behaviour (no
PayPal) is the **control**; add one variation named `show-paypal`.

Your code will branch on the variation _name_, not the flag value, so keep names short and stable.

## 2. Create the metric

With a [warehouse connected](/experimentation/connect-a-warehouse), [create a metric](/experimentation/create-metrics):

- **Name**: Checkout Completion
- **Measure**: Occurrence
- **Direction**: Higher is better
- **Event name**: `checkout_completed`

## 3. Create the experiment

[Create an experiment](/experimentation/create-an-experiment) on `paypal_button`:

- **Hypothesis**: _"Offering PayPal at checkout will increase checkout completion by at least 10% within 30 days."_
- **Rollout**: 10%, split evenly. 5% of identities see PayPal, 5% act as control, and the remaining 90% stay out of the
  experiment entirely.
- **Primary metric**: Checkout Completion, expected to **increase**.

Launch it from the Review step.

## 4. Instrument the checkout

On the checkout page, resolve the flag (recording the exposure) and branch on the variation name. When a checkout
completes, send the conversion event. The SDK must be initialised with `enableEvents: true` and the user identified; see
[Run an Experiment](/experimentation/run-an-experiment).

```tsx
import flagsmith from '@flagsmith/flagsmith';
import { useExperiment } from '@flagsmith/flagsmith/react';

const CheckoutPage: React.FC = () => {
 // Evaluates the flag and records the exposure
 const flag = useExperiment('paypal_button');
 const showPaypal = flag?.enabled && flag?.variant === 'show-paypal';

 const onOrderConfirmed = () => {
  // Record the conversion
  flagsmith.trackEvent('checkout_completed');
 };

 return (
  <>
   <CardPaymentForm onConfirmed={onOrderConfirmed} />
   {showPaypal ? <PayPalButton onConfirmed={onOrderConfirmed} /> : null}
  </>
 );
};
```

Outside React, `flagsmith.getExperimentFlag('paypal_button')` does the same job as the hook. The same flow works in
Python; see [Run an Experiment](/experimentation/run-an-experiment) for both SDKs.

If checkout is available to visitors who aren't logged in, identify them with a persistent anonymous GUID so bucketing
and events stay consistent; see [Identities](/flagsmith-concepts/identities).

## 5. Read the results and roll out

On the experiment page, check the **Exposures** panel: enrolment should track about 10% of your identities, split 50/50.
Then watch the results as conversions arrive; see [Analyse an Experiment](/experimentation/analyse-an-experiment).

When the result is conclusive, end the experiment, roll the PayPal button out to everyone, and clean up the flag.
