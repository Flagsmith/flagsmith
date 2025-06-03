---
title: Sentry Integration
description: Integrate Flagsmith with Sentry
sidebar_label: Sentry
hide_title: true
---

![Sentry logo](/img/integrations/sentry/sentry-logo.svg)

Integrate Flagsmith with Sentry to enable feature flag
[Change Tracking](https://docs.sentry.io/product/issues/issue-details/feature-flags/#change-tracking).

:::tip

Along with _Change Tracking_, Sentry also offers
[Evaluation Tracking](https://docs.sentry.io/product/issues/issue-details/feature-flags/#evaluation-tracking).
Integrating with _Evaluation Tracking_ is currently only possible via our
[OpenFeature provider](/clients/openfeature.md).

:::

## Integration Setup

1. **In Sentry**
   1. Visit the
      [feature flags settings page](https://sentry.io/orgredirect/organizations/:orgslug/settings/feature-flags/change-tracking/)
      in a new tab.
   1. Click the "Add New Provider" button.
   1. Select "Generic" in the dropdown that says "Select a provider".
   1. Copy the provided Sentry webhook URL — we'll use that soon.
   1. **Do not close this page!** We're not done yet.
1. **In Flagsmith**
   1. Go to Integrations > Sentry > Add Integration.
   1. Choose the Environment from which Sentry will receive feature flag change events.
   1. Paste the URL copied above into "Sentry webhook URL".
   1. Copy the secret from "Webhook secret".
   1. Click "Save". ✅
1. **Back to Sentry**
   1. Paste the secret copied above.
   1. Click "Add Provider". ✅

Flag change events will now be sent to Sentry, and should be displayed in issue details. For more information, visit
Sentry's [Issue Details page documentation](https://docs.sentry.io/product/issues/issue-details/#feature-flags).
