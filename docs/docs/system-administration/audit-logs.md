---
title: Audit Logs
---

Every action taken within the Flagsmith administration application is tracked and logged. This allows you to easily
retrace the events and values that flags, identities and segments have taken over time.

You can view the Audit Log within the Flagsmith application, and filter it in order to find the information you are
after.

## Audit Log Web Hooks

You can also stream your Audit Logs into your own infrastructure using
[Audit Log Web Hooks](/system-administration/webhooks#audit-log-web-hooks).

## Event Types

Flagsmith records the following events into the Audit Log.

### Environments

- New environment created within a Project
- Environment meta-data updated

### Flags

- New Flag created
- Flag state changed
- Flag deleted
- Multivariate flag state changed

### Segments

- New Segment created
- Segment rule updated
- Segment condition added
- Segment condition updated
- Segment overrides re-ordered

### Identities

- Identity feature state overridden
