# Release Pipelines

:::warning

Release Pipelines is currenlty in alpha phase and is not available to the public.

:::


Release Pipelines allow you to define a series of stages that your feature flags progress through automatically. Each stage can have specific triggers and actions that control when and how flags are released.

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

1. **Stage Name**: A descriptive name for the stage (e.g., "Development", "Staging", "Production", "Turn on beta users").
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
A release pipeline is inactive and does not process feature flags
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

### From the Dashboard

1. Navigate to your feature flags.
2. Select the flag you want to add to a pipeline.
3. Click the **Add to Release Pipeline** option.
4. Select the pipeline.
5. Confirm the selection.

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

### Viewing Audit Logs

You can view these audit events in your project's audit log:
1. Navigate to your project.
2. Go to the **Audit Log** tab.

