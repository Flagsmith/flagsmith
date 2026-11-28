---
title: Common Anti-patterns
sidebar_label: Common Anti-patterns
sidebar_position: 10
---

# Common Anti-patterns

A flag works best when it answers one small question. The patterns below add work without making that question easier to
answer. Each section names the problem and gives a different way to handle it.

## Expecting real-time updates to change the screen

A real-time event tells your app that a flag changed. It does not change what the user sees. Your app still has to
refetch flags, handle requests already in flight, and decide what happens to a screen that is partway through a render.
Teams often add real-time updates first and write that code later.

Fetch flags when the session starts. That is enough for most applications. If a feature needs updates during a session,
use [real-time flags](/performance/real-time-flags) and plan for the refetch logic. Internal dashboards, kiosks,
monitoring screens, and emergency kill switches justify the extra code.

## Chaining flags

Flagsmith supports [flag dependencies](/managing-flags/flag-dependencies), so one flag can depend on another. A long
chain is hard to reason about. Each extra link adds a state you have to simulate before you know what a user will see. A
broken prerequisite can also turn off a feature that looks unrelated.

Put the condition in one flag and use segments and traits to describe who should see it. Use dependencies for a short,
explicit prerequisite, such as a shared platform service that must exist before a feature can run.

## Storing HTML in remote config

HTML in a flag value couples your content to a release switch. Editors cannot preview it, translators cannot work with
it, and a small change can break the page layout. The flag then becomes a publishing tool that nobody maintains.

Store the markup in a content management system. Keep the flag for the decision to show or hide that content.

## Storing translated strings in flags

A flag value is not a translation system. Each new language adds another value to edit, and the copy drifts away from
the rest of your interface. Product teams also have to know where the strings live before they can change them.

Use your content management system or localisation tooling for text. Use the flag to turn the translated feature on for
a group of users.

## Adding Edge Proxy before you need it

[Edge Proxy](/performance/edge-proxy) puts evaluation close to your users. It also adds a service to deploy, monitor,
and debug. If your users are in one region and the API already meets your latency target, the extra service buys little.

Measure the problem first. Record where requests come from and how long the API takes. Adopt Edge Proxy when you have a
geographic spread or a measured latency need.

## Using PII as a trait or identifier

Client-side SDK endpoints are public. An email address or phone number stored as a persistent trait can be read by
anyone who guesses the identity. Using personal data as the identity makes that worse, since the identifier travels with
every flag request.

Use a GUID or another unguessable value as the identity. See [Identities](/flagsmith-concepts/identities). When you need
personal data for a targeting decision, send it as a [transient trait](/flagsmith-concepts/identities#transient-traits)
so Flagsmith evaluates it without storing it.

## Wrapping the SDK for portability

A wrapper around one SDK does not make your code portable to another flag provider. You still call provider-specific
methods, and you own the wrapper when the SDK changes.

Use [OpenFeature](/integrating-with-flagsmith/openfeature) when portability is the goal. It gives you one interface
across providers. If you want shorter names or project-specific helpers, wrap OpenFeature instead.

## Changing flags in production without review

One person can turn on a flag in production and change what every user sees. No second check stands between the click
and the release.

Enable [Change Requests](/administration-and-security/governance-and-compliance/change-requests) for production
environments. Reviewers see the exact change before it goes live. Keep direct edits for development environments.
