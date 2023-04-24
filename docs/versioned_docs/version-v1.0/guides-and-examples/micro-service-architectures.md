---
title: Feature Flags and the Micro-Service Architecture
---

## The Problem

Sometimes it can be tricky to figure out how to map Flagsmith Projects to your own Applications. When you are working on
an application that has 1 core server-side service, it's generally fairly obvious to map 1 Flagsmith Project to your
server-side application.

Things get a bit more tricky when you start working with a micro-service architecture. Let's say you have 5
micro-services that are all employed to power your front end application. Should you create a single Flagsmith Project
to cover all 5 services? Or 5 Projects, one for each service? Or maybe some number in between?

## The Solution

Like a lot of problems in Software Engineering, the right answer is "it depends". Maybe not the most helpful answer, but
easily the most accurate! What it boils down to is coupling.

Generally if we are looking at a collection of micro-services that are tightly coupled, they may well be a good
candidate for sharing a single Flagsmith project. On the other had, if your services are loosely coupled with will
defined interface boundaries, you will probably want to go with mapping 1 Flagsmith project to 1 micro-service.

### Why though?

It really boils down to interface boundaries. If you are writing a service that has an agreed upon, established API
interface, the services consuming your API really don't care too much about your implementation. That being the case, by
definition they shouldn't really care about your feature flags either. Why would they?

On the other hand, if you are working on a service that is tightly coupled with another, you probably do care about
their flags. Let's take an example. Imagine three micro-services that share a common database. You want to make a schema
change to the database, but that means coordinating the new schema code amongst your 3 services. Coordinating
deployments is fraught with danger, but using feature flags is a great solution to this problem. In this case, having
the 3 micro-services sharing the 1 flagsmith project is really helpful

### Other things to consider

If you have a single Flagsmith project powering several micro-services, you need to be aware of the following aspects.

All the team members of the project will have access to your flags. If an engineer on another team doesn't really have
any business managing your production flags, it might be a sign to split out into 2 Flagsmith projects.

It can be helpful for segment definitions to be shared amongst micro-services. That would point to having a single
Flagsmith project. If the context that your users access your service is the same/similar, sharing segments makes a lot
of sense.
