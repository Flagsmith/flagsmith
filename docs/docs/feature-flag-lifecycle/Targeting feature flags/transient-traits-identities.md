---
title: Using Transient Traits and Identities
---
# Using Transient Traits and Identities

## Overview
By the end of this tutorial, you'll be able to use transient traits and identities in Flagsmith to evaluate feature flags for anonymous or privacy-sensitive users, without storing their data.


**Prerequisites:**
- A Flagsmith project and environment set up
- Basic knowledge of feature flags and traits
- Access to a Flagsmith SDK (e.g., JavaScript)


## Background
Transient traits and identities allow you to evaluate feature flags for users without persisting their data. This is useful for privacy, compliance, and temporary/anonymous user scenarios.


## Before You Begin
- Ensure you have a Flagsmith account and project.
- Install the Flagsmith SDK for your platform (e.g., `npm install flagsmith` for JavaScript).
- Obtain your environment key from the Flagsmith dashboard.


## Steps

### 1. Initialize the SDK
```javascript
import flagsmith from 'flagsmith';

flagsmith.init({
  environmentID: 'YOUR_ENVIRONMENT_KEY',
});
```

### 2. Evaluate a Feature Flag with a Transient Trait
Suppose you want to target users based on their email domain, but don’t want to store their email.

```javascript {5}
flagsmith.updateContext({
  identity: {
    identifier: 'user-123',
    traits: {
      email: { value: 'alice@example.com', transient: true },
    },
  },
});
```
The flag evaluation will use the email trait, but Flagsmith will not store it.

### 3. Evaluate a Feature Flag for an Anonymous User
You can use a transient identity for a guest or temporary session:

```javascript 2
flagsmith.init({
  evaluationContext: {
    identity: {
      identifier: null,
      traits: {
        sessionStartTime: { value: Date.now(), transient: true },
      },
    },
  },
});
```
Flags are evaluated for this session, but no identity or trait is stored.

### 4. Combine Multiple Transient Traits
You can send several transient traits for complex targeting:

```javascript {5-7}
flagsmith.updateContext({
  identity: {
    identifier: 'visitor-456',
    traits: {
      location: { value: 'US', transient: true },
      cartValue: { value: 299.99, transient: true },
      pageViews: { value: 5, transient: true },
    },
  },
});
```



## Summary
You’ve learned how to:
- Use transient traits to evaluate feature flags without storing sensitive data
- Target anonymous or temporary users with transient identities
- Combine multiple transient traits for advanced targeting


## Next Steps
- Explore [Flagsmith SDK documentation](https://docs.flagsmith.com/clients/)
- Try using transient traits in your own app
- Review your privacy requirements and update your flag targeting accordingly

:::tip
Consider using transient traits for:
- User location data
- Session information
- Temporary preferences
- Testing scenarios
:::

:::important
Transient traits are evaluated in real-time and cannot be used for historical analysis since they are not stored.
:::