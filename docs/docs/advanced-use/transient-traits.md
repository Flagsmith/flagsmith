---
title: Transient Traits and Identities
---

By default, Flagsmith [stores all Traits](/basic-features/managing-identities#identity-and-trait-storage) associated
with an Identity to evaluate flags. This default behavior works for most use cases. However, there are scenarios where
you may want more control over which Traits or Identities are stored. Using the Flagsmith API and SDKs, you can mark
Traits and Identities as transient — meaning they are used for flag evaluation but are not stored.

## Overview and Use Cases

Transient Identities and Traits are particularly useful when you need to run flag evaluations without storing specific
data in Flagsmith. Below are common scenarios where transient Traits or Identities come in handy.

### Anonymous Identities

If you choose to provide an empty or blank (`""`) identifier is provided, Flagsmith will automatically treat the
Identity as transient. In this case, an auto-generated identifier is returned, based on a hash of the provided Traits.
This ensures consistent flag evaluations without persisting the Identity in the Flagsmith dashboard.

```javascript
flagsmith.init({
 evaluationContext: {
  identity: {
   identifier: null,
   traits: { paymentPreference: 'cash' },
  },
 },
});
let identifierToUseLater = flagsmith.getContext().identity.identifier;
```

This approach is useful for scenarios such as A/B testing in e-commerce, where you want to include users who haven't
registered or logged in.

### Ephemeral Contexts

In some cases, you may need to temporarily override certain Traits for a session or device without overwriting the
stored value. For example, imagine you’ve persisted the `screenOrientation` Trait as `landscape` for a user:

```javascript
flagsmith.init({
 evaluationContext: {
  identity: {
   identifier: 'my-user',
   traits: { screenOrientation: 'landscape' },
  },
 },
});
```

If you want to switch the `screenOrientation` to `portrait` for a specific session without overwriting the existing
value, you can mark the Trait as transient:

```javascript
flagsmith.setTrait('screenOrientation', { value: 'portrait', transient: true });
```

In this case, `portrait` will be used for one specific flag evaluation, but the stored `landscape` value will remain
unchanged.

### Skipping Personal Identifiable Information (PII)

You can mark sensitive Traits, such as `email`, `phoneNumber`, or `locality`, as transient to enable segmentation
without storing the actual data. For example, you may want to target users based on email domains while avoiding the
storage of email addresses.

Considering you have a Segment condition where `"email"` ends with `"example.com"`. To get flags for this Segment:

```javascript
flagsmith.updateContext({
 identity: {
  identifier: 'test-user-with-transient-email',
  traits: {
   email: { value: 'alice@example.com', transient: true },
  },
 },
});
```

After making the SDK call, if you check the Identities tab, you'll see the `test-user-with-transient-email` Identity
without the `email` Trait being stored.
