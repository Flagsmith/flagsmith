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

## Change Tracking Setup

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
   1. Insert a secret (10-60 characters) and copy it.
   1. Click "Save". ✅
1. **Back to Sentry**
   1. Paste the secret copied above.
   1. Click "Add Provider". ✅

Flag change events will now be sent to Sentry, and should be displayed in issue details. For more information, visit
Sentry's [Issue Details page documentation](https://docs.sentry.io/product/issues/issue-details/#feature-flags).

## Evaluation Tracking example

In order to add **evaluated** feature flags to a Sentry issue when it occurs, events must be sent via Sentry SDK, i.e.
the same SDK used to send application errors to Sentry.

Flagsmith relies on the OpenFeature SDK and its integration with Sentry.

### Python

Sentry offers [good documentation](https://docs.sentry.io/platforms/python/integrations/openfeature/) on how to
integrate the Sentry SDK with the OpenFeature SDK. We'll extend it a bit adding an example of using it with Flagsmith.

You'll need to install the following libraries:

```sh
pip install "sentry-sdk[openfeature]"
pip install openfeature-provider-flagsmith
```

The following snippet is a micro-application that reports feature flags to Sentry when an exception is raised.

```python
import flagsmith
import sentry_sdk
from openfeature import api as of_api
from openfeature_flagsmith.provider import FlagsmithProvider
from sentry_sdk.integrations.openfeature import OpenFeatureIntegration

app = flask.Flask(__name__)

flagsmith_client = flagsmith.Flagsmith(
    environment_key='<public environment key>',
)

feature_flag_provider = FlagsmithProvider(
    client=flagsmith_client,
)

of_api.set_provider(feature_flag_provider)

sentry_sdk.init(
    dsn="<Sentry DSN>",
    send_default_pii=True,
    integrations=[
        OpenFeatureIntegration(),
    ]
)

def apply_discount(price):
    of_client = of_api.get_client()
    is_discount_enabled = of_client.get_boolean_value('discount_enabled', False)
    if is_discount_enabled:
        discount = price / 0  # ZeroDivisionError
    else:
        discount = None
    return price * discount  # TypeError
```

You can learn more about feature flags and Sentry issues in their
[Issue Details documentation](https://docs.sentry.io/product/issues/issue-details/#feature-flags).

## JavaScript

You'll need to manually call `Sentry.FeatureFlagsIntegration.addFeatureFlag` when evaluating a feature flag. Learn more
in the [Sentry documentation](https://docs.sentry.io/platforms/javascript/configuration/integrations/featureflags/).
