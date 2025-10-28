---
title: "Deployment and Self-hosting Overview"
description: "Learn how to deploy and self-host Flagsmith in your own infrastructure."
sidebar_position: 1
---

# Deployment and Self-hosting

Welcome to the Flagsmith deployment and self-hosting guide. This section provides comprehensive information on how to deploy and manage your own Flagsmith instance in your infrastructure.

## What is Self-hosting?

Self-hosting Flagsmith allows you to run the complete Flagsmith platform within your own infrastructure, giving you full control over your data, security policies, and deployment environment. This is ideal for organisations that require:

- **Data sovereignty**: Keep your feature flag data within your own infrastructure
- **Custom integrations**: Integrate with your existing tooling and workflows
- **Enhanced security**: Implement your own security policies and compliance requirements
- **Offline capabilities**: Deploy in environments with limited or no internet access

## Deployment Options

Flagsmith supports multiple deployment methods to suit different infrastructure requirements:

### Quick Start Options
- **[One-click installers](/deployment-self-hosting/hosting-guides/one-click-installers)**: Get up and running quickly with pre-configured deployment options
- **[Docker deployment](/deployment-self-hosting/hosting-guides/docker)**: Containerised deployment using Docker and Docker Compose
- **[Manual installation](/deployment-self-hosting/hosting-guides/manual-installation)**: Step-by-step installation guide for custom deployments

### Cloud Platform Support
- **[AWS deployment](/deployment-self-hosting/hosting-guides/cloud-providers/aws)**: Deploy on Amazon Web Services
- **[Google Cloud Platform](/deployment-self-hosting/hosting-guides/cloud-providers/google-cloud)**: Deploy on Google Cloud Platform
- **[Aptible](/deployment-self-hosting/hosting-guides/cloud-providers/aptible)**: Deploy on Aptible platform

### Enterprise Orchestration
- **[Kubernetes and OpenShift](/deployment-self-hosting/hosting-guides/kubernetes-openshift)**: Full Kubernetes deployment with Helm charts and operators
- **[Enterprise Edition](/deployment-self-hosting/enterprise-edition)**: Additional features and capabilities for enterprise deployments

## Core Configuration

Once deployed, you'll need to configure your Flagsmith instance:

- **[Initial Setup](/deployment-self-hosting/core-configuration/initial-setup)**: Create your first superuser and initialise the platform
- **[Environment Variables](/deployment-self-hosting/core-configuration/environment-variables)**: Configure application settings and connections
- **[Email Setup](/deployment-self-hosting/core-configuration/email-setup)**: Configure email notifications and password resets
- **[Caching Strategies](/deployment-self-hosting/core-configuration/caching-strategies)**: Optimise performance with Redis and other caching options
- **[Running Flagsmith on Flagsmith](/deployment-self-hosting/core-configuration/running-flagsmith-on-flagsmith)**: Use Flagsmith to manage Flagsmith itself

## Scaling and Performance

As your usage grows, you'll need to consider scaling and performance:

- **[Sizing and Scaling](/deployment-self-hosting/scaling-and-performance/sizing-and-scaling)**: Understand resource requirements and scaling strategies
- **[Monitoring](/deployment-self-hosting/scaling-and-performance/monitoring)**: Set up monitoring and alerting for your deployment
- **[Asynchronous Task Processor](/deployment-self-hosting/scaling-and-performance/asynchronous-task-processor)**: Configure background task processing
- **[Using InfluxDB for Analytics](/deployment-self-hosting/scaling-and-performance/using-influxdb-for-analytics)**: Set up analytics storage
- **[Load Testing](/deployment-self-hosting/scaling-and-performance/load-testing)**: Test your deployment under load

## Administration and Maintenance

Ongoing administration tasks to keep your deployment running smoothly:

- **[Using the Django Admin](/deployment-self-hosting/administration-and-maintenance/using-the-django-admin)**: Access and manage your deployment through the admin interface
- **[Upgrades and Rollbacks](/deployment-self-hosting/administration-and-maintenance/upgrades-and-rollbacks)**: Safely upgrade your deployment and roll back if needed
- **[Troubleshooting](/deployment-self-hosting/administration-and-maintenance/troubleshooting)**: Common issues and their solutions

## Edge Proxy

For high-performance deployments:

- **[Edge Proxy](/deployment-self-hosting/edge-proxy)**: Deploy edge proxies for improved performance and reduced latency

## Getting Started

To get started with self-hosting Flagsmith:

1. **Choose your deployment method**: Start with [Docker](/deployment-self-hosting/hosting-guides/docker) for a quick setup, or use [one-click installers](/deployment-self-hosting/hosting-guides/one-click-installers) for cloud platforms
2. **Configure your environment**: Set up [environment variables](/deployment-self-hosting/core-configuration/environment-variables) and [email configuration](/deployment-self-hosting/core-configuration/email-setup)
3. **Initialise your instance**: Create your first superuser using the [initial setup guide](/deployment-self-hosting/core-configuration/initial-setup)
4. **Scale as needed**: Monitor your deployment and scale using the [scaling guides](/deployment-self-hosting/scaling-and-performance/sizing-and-scaling)

## Support

If you encounter issues during deployment or need assistance with enterprise features, please refer to our [troubleshooting guide](/deployment-self-hosting/administration-and-maintenance/troubleshooting) or contact our support team.

For enterprise deployments with additional features and support, consider the [Enterprise Edition](/deployment-self-hosting/enterprise-edition). 