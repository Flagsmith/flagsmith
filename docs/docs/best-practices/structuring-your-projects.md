---
title: Structuring Your Projects
sidebar_label: Structuring Your Projects
sidebar_position: 8
---

One of the first decisions you'll make when adopting Flagsmith is how to structure your projects. This guide helps you answer the question: **"How do I logically separate my teams, services and microservices into different projects?"**

## Understanding Flagsmith's data model

Before diving into recommendations, it's helpful to understand how Flagsmith organises your feature flags:

- **Organisations** are the top level and contain your team members and projects.
- **Projects** contain your features and environments. Features are defined once per project and shared across all environments within that project.
- **Environments** (such as Development, Staging, Production) allow you to have different flag states for the same feature.

For more details, see the [Data Model](/flagsmith-concepts/data-model) documentation.

## When to create separate projects

Consider creating separate projects when:

- **Different teams own different services.** If teams work independently and don't need to coordinate flag changes, separate projects provide cleaner boundaries and simpler permission management.
- **Services have different release cycles.** Separate projects allow teams to manage their flags without affecting other services.
- **You need distinct access control.** With separate projects, you can grant teams full access to their own flags whilst restricting visibility of other projects.
- **Features are truly independent.** If there's no need for flags to be shared or coordinated between services, separate projects reduce clutter.

## When to use a single project

Consider using a single project when:

- **Services are tightly coupled.** If multiple services need to coordinate changes, sharing flags in a single project can make this easier and safer.
- **You share user context across services.** A single project allows you to define [Segments](/flagsmith-concepts/segments) once and use them across all services, rather than duplicating segment definitions.
- **You want a unified view of your feature flags.** A single project gives you visibility of all active flags and their states in one place.
- **You're a small team.** With fewer people and services, the simplicity of a single project often outweighs any organisational benefits of multiple projects.

## Microservice architectures

If you're running a microservice architecture, the decision depends on how coupled your services are.

**Tightly coupled services** are good candidates for sharing a single Flagsmith project. For example, if multiple services share a database and you need to coordinate a schema change, using a single project with shared flags makes this much easier than coordinating deployments across separate projects.

**Loosely coupled services** with well-defined interface boundaries are generally better suited to one project per service. If a service's API is stable, consuming services don't need to know about its internal feature flags.

For more details on how project structure affects API usage, see [Micro-service Architectures](/best-practices/efficient-api-usage#micro-service-architectures).

## Multiple teams

When you have many teams, there are two main approaches:

### One project per team

This approach works well when:

- Teams have clear ownership boundaries
- Teams work independently with minimal coordination
- You want to simplify access control (each team manages their own project)

### Projects organised by domain

This approach works well when:

- Multiple teams contribute to the same service or domain
- You need to coordinate flag changes across teams
- Teams share common segments or user context

In practice, many organisations use a hybrid approach: separate projects for truly independent services, but shared projects where teams need to collaborate.

## Practical considerations

### System limits

Each project has [system limits](/administration-and-security/governance-and-compliance/system-limits) on features and segments.

A well-scoped project should rarely approach these limits. Most feature flags are designed to be temporary, they serve their purpose during a release or experiment and should then be removed. If you find yourself nearing these limits, it's often a sign that stale flags need to be cleaned up or that your project scope is too broad. For guidance on managing flag removal, see [Flag Lifecycle](/best-practices/flag-lifecycle).

### Access control

Flagsmith's [Role-based access control (RBAC)](/administration-and-security/access-control/rbac) operates at the project and environment level. If you need fine-grained permissions (for example, allowing some users to only modify certain flags), consider:

- Using [feature tags](/managing-flags/tagging) with tagged permissions to control access within a project
- Separating concerns into different projects where each team has full access

### Shared segments

[Segments](/flagsmith-concepts/segments) are defined at the project level. If multiple services need to target the same user groups, using a single project allows you to define the segment once. With separate projects, you would need to recreate the segment in each project.

## Recommendations summary

| Scenario | Recommendation |
| --- | --- |
| Small team, few services | Start with a single project |
| Independent microservices with stable APIs | One project per service |
| Tightly coupled services (shared database, coordinated releases) | Single shared project |
| Multiple teams needing separate permissions | Consider separate projects per team or domain |
| Shared user segments across services | Single project to share segment definitions |
| Approaching system limits | Split into multiple projects by domain |

## Getting started

If you're unsure, start with fewer projects rather than more. It's easier to split a project later than to merge multiple projects. Begin with a structure that matches your current team and service boundaries, and adjust as your organisation grows.
