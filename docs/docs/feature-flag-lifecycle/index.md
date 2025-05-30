---
title: Feature Flag lifecycle
sidebar_position: 3
---

# Understanding Flag Management

Feature flags in Flagsmith can be managed throughout their entire lifecycle - from creation to retirement. Understanding how to effectively manage flags is crucial for maintaining a clean codebase and ensuring proper feature delivery.

## Short-Lived Flags

Short-lived flags are intended to be removed from your code and from Flagsmith after serving their purpose. Their typical lifecycle:

1. Create the flag in Flagsmith.
2. Add the flag to your application code.
3. Toggle the flag and/or apply segment overrides to control application behavior.
4. Once finished, remove the flag from your codebase.
5. Deploy your application so there are no references to the flag.
6. Remove the flag from Flagsmith.

**Common use cases:**
- **Feature Roll-Outs:** Decouple deployment from release. Remove the flag once the feature is fully rolled out. This is particularly valuable for:
  - Mobile apps where App/Play Store approval times can delay fixes
  - Gradual user base exposure using staged rollouts
  - Beta testing with specific user segments
- **Experimentation:** Use multi-variate flags for A/B or multivariate tests. Remove the flag after the experiment is complete.

:::tip Best Practice
For mobile applications, feature flags are especially important because of the delay in getting updates to users:
1. App store approval times
2. User update adoption periods (can take weeks/months)
Using feature flags lets you quickly disable problematic features without waiting for app store approval.
:::

## Long-Lived Flags

Long-lived flags may exist for the lifetime of your application. They serve different purposes:

### Kill Switches
Kill switches let you remotely disable features or entire application areas. They are maintained long-term for emergencies such as:
- Disabling problematic features quickly
- Managing application access during maintenance
- Controlling system load by turning off resource-intensive features

### Feature Management Flags
These flags control ongoing feature access and configuration:
- Use segments to manage feature access by user plan/tier
- Control feature availability based on user traits
- Configure feature behavior without code changes

:::important
While short-lived flags should be removed when no longer needed, long-lived flags are part of your application's architecture and should be maintained carefully.
:::

## Managing Flag Lifecycle

To effectively manage your feature flags:

1. **Document the Intent**: Clearly mark flags as short-lived or long-lived when creating them
2. **Use Tags**: Tag flags by their lifecycle status (e.g., `temporary`, `kill-switch`, `permanent`)
3. **Regular Cleanup**: Periodically review and remove unused short-lived flags
4. **Version Control**: Remove flag code from your codebase only after the flag is fully retired

By understanding and managing the lifecycle of your feature flags, you can ensure your codebase remains maintainable and your feature management practices stay effective.