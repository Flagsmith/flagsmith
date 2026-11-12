---
title: Release Pipelines
sidebar_label: Release Pipelines
sidebar_position: 4
---

:::info

Release Pipelines is currently in a closed beta, please contact support@flagsmith.com if you'd like to gain access.

:::

![Use Case](/img/release-pipelines/use-case-pipeline.png)

Release Pipelines act as your intelligent release assistant, automating your entire feature flag deployment process.
Define stages that your flags progress through automatically, with triggers and actions that control rollouts to
selected environments and audiences. Release Pipelines can automatically generate change requests when promoting flags
to production, eliminating manual effort and streamlining your deployment workflow.

## Key Benefits

- **Automated Deployments**: Reduce manual intervention by automating flag releases across environments.
- **Standardised Process**: Ensure consistent release protocols across your team.
- **Reduced Risk**: Control the pace of rollouts with customisable conditions.
- **Better Visibility**: Track the progress of your feature releases through each stage.

## Creating a Release Pipeline

### Step 1: Navigate to Release Pipelines

![On Enter](/img/release-pipelines/create-release-pipeline.png)

1. Go to your project in the Flagsmith dashboard.
2. Navigate to the **Release Pipelines** section.
3. Click **Create Release Pipeline**.

### Step 2: Configure Pipeline Settings

![On Enter](/img/release-pipelines/pipeline-configuration.png)

**Pipeline Information:**

- **Name**: Give your pipeline a descriptive name (e.g., "Web App Release Pipeline").

**Pipeline Configuration:**

- Add multiple stages to represent your release process.
- Each stage can represent an environment or phase in your release process.

## Pipeline Stages

### Stage Configuration

Each stage in your pipeline consists of:

1. **Stage Name**: A descriptive name for the stage (e.g., "Development", "Staging", "Production", "Turn on beta
   users").
2. **Trigger**: When the stage should be activated.
3. **Actions**: What should happen when the stage is triggered.

### Stage Triggers

**On Enter** (`ON_ENTER`)

![On Enter](/img/release-pipelines/on-enter.png)

- Triggers immediately when a flag is added to this stage.
- Use this for immediate actions when flags reach a particular stage.

**Wait For** (`WAIT_FOR`)

![Wait For](/img/release-pipelines/wait-for.png)

- Triggers after waiting for a specified amount of time.
- Configure the wait time in minutes, hours, or days.
- Use this for gradual rollouts or testing periods.
- Optionally, add an [abort condition](#aborting-a-pipeline-when-a-flag-becomes-unhealthy) to stop the release if the
  flag becomes unhealthy during the wait.

### Stage Actions

![Wait For](/img/release-pipelines/actions.png)

**Toggle Feature Actions:**

- **Enable flag for everyone**: Enables the feature flag for all users in the environment.
- **Disable flag for everyone**: Disables the feature flag for all users in the environment.
- **Enable flag for segment**: Enables the feature flag for a specific user segment.
- **Disable flag for segment**: Disables the feature flag for a specific user segment.

## Publishing a Release Pipeline

### Draft Status

After a release pipeline is created and before it is published, it remains in draft mode. In this state:

- The release pipeline is inactive and does not process feature flags.
- The configuration remains editable.
- You can modify stages, triggers, and actions freely.
- Once published, the pipeline becomes immutable and operational.

### Publishing Process

:::warning

Once published, a release pipeline cannot be modified. Ensure your configuration is correct before publishing.

:::

1. Complete your pipeline configuration.
2. Review all stages, triggers, and actions.
3. Click **Publish Pipeline**.
4. Confirm the action when prompted.

![Publish Release Pipeline](/img/release-pipelines/publish-release-pipeline.png)

## Adding Flags to Release Pipelines

:::warning

In alpha phase there are no automatic rollbacks, you'd need to revert changes manually. To stop a release automatically,
use an [abort condition](#aborting-a-pipeline-when-a-flag-becomes-unhealthy).

:::

### From the Dashboard

1. Navigate to your feature flags.
2. Select the flag you want to add to a pipeline.
3. Click the arrow on the "Update Feature Value" button to expand options.
4. Click the **Add to Release Pipeline** option.
5. Select the pipeline.
6. Confirm the selection.

![Add To Release Pipeline](/img/release-pipelines/add-to-release-pipeline.png)

### Pipeline Execution

Once a flag is added to a pipeline:

- It starts at the first stage you specified.
- The pipeline automatically executes based on your configured triggers.
- Actions are performed according to your stage configuration.
- The flag progresses through each stage in sequence.

## Managing Release Pipelines

### Viewing Pipeline Status

![View Pipeline](/img/release-pipelines/view-pipeline.png)

- **Active Pipelines**: View all published pipelines and their current status.
- **Flag Progress**: Track which flags are currently in each stage.

### Aborting a Pipeline When a Flag Becomes Unhealthy

A **Wait For** stage can act as a kill switch. Tick **Abort if unhealthy in this environment**. If
[Feature Health](/managing-flags/feature-health-metrics) reports the flag as unhealthy in the stage's environment while
it waits, the pipeline stops and the flag is turned off in that environment. If the wait runs out and the flag is
healthy, the stage runs its actions and the flag moves to the next stage as usual.

**Example: release to everyone unless an alert fires**

1. **Production (beta)**: _On Enter_, enable the flag for the `beta` segment.
2. **Production (everyone)**: _Wait For_ 1 hour, abort if unhealthy, then enable the flag for everyone.

The pipeline aborts if the flag:

- becomes unhealthy in the stage's environment while it waits in the stage; or
- is already unhealthy in the stage's environment when it enters the stage.

Health is checked per environment, so an alert in Staging doesn't abort a Production stage. An unhealthy event that
doesn't name an environment counts as unhealthy in every environment. Dismissed alerts don't count.

When the pipeline aborts:

- The flag is **disabled for everyone in the stage's environment**. This covers the environment default and every
  segment override, including overrides set by earlier stages. Flag values are not changed.
- The change is published as a new version of the flag, so it appears in the flag's version history.
- The flag is removed from the pipeline. You can add it to a pipeline again once you've fixed the issue.
- Other environments are not changed.
- An entry is added to the audit log, and the stage notification email says the pipeline was aborted and why.

:::note

- The abort condition needs a [Feature Health provider](/managing-flags/feature-health-metrics) set up for the project.
  Without one, flags are never reported unhealthy and the stage won't abort.
- An abort can't be undone. The pipeline doesn't resume if the flag becomes healthy again.
- Abort conditions are only available on **Wait For** stages. They don't apply to stages that have already finished, or
  to phased rollouts.
- Identity overrides are not changed when a pipeline aborts.

:::

### Removing Flags from Pipelines

If you need to remove a flag from a pipeline:

1. Navigate to the flag or pipeline view.
2. Select **Remove from Release Pipeline**.
3. Confirm the action.

## Audit Log Events

Release Pipelines generate audit log events to track pipeline-related activities.

### Events

**Pipeline Creation**

- Event: `RELEASE_PIPELINE_CREATED_MESSAGE`.
- Triggered when a new release pipeline is created.

**Pipeline Publication**

- Event: `RELEASE_PIPELINE_PUBLISHED_MESSAGE`.
- Triggered when a pipeline is published and becomes active.

**Pipeline Deletion**

- Event: `RELEASE_PIPELINE_DELETED_MESSAGE`.
- Triggered when a pipeline is permanently deleted.

**Feature Addition to Pipeline**

- Event: `RELEASE_PIPELINE_FEATURE_ADDED_MESSAGE`.
- Triggered when a feature flag is added to a release pipeline.

**Feature State Updates**

- Event: `FEATURE_STATE_UPDATED_BY_RELEASE_PIPELINE_MESSAGE`.
- Triggered when a pipeline automatically updates a feature flag's state during stage execution.

**Pipeline Aborted**

- Event: `RELEASE_PIPELINE_ABORTED_MESSAGE`.
- Triggered when a flag becomes unhealthy in a stage with an abort condition and the pipeline turns the flag off.

### Viewing Audit Logs

You can view these audit events in your project's audit log:

1. Navigate to your project.
2. Go to the **Audit Log** tab.
