# Release Pipelines

Release Pipelines allow you to define a series of stages that your feature flags progress through automatically, from development to production. Each stage can have specific triggers and actions that control when and how flags are released.

:::info

Release Pipelines are available on [Enterprise plans](/version-comparison.md#enterprise-benefits).

:::

## Key Benefits

- **Automated Deployments**: Reduce manual intervention by automating flag releases across environments
- **Standardised Process**: Ensure consistent release protocols across your team
- **Reduced Risk**: Control the pace of rollouts with customisable conditions
- **Better Visibility**: Track the progress of your feature releases through each stage

## Creating a Release Pipeline

### Step 1: Navigate to Release Pipelines

1. Go to your project in the Flagsmith dashboard
2. Navigate to the **Release Pipelines** section
3. Click **Create Release Pipeline**

### Step 2: Configure Pipeline Settings

**Pipeline Information:**
- **Name**: Give your pipeline a descriptive name (e.g., "Web App Release Pipeline")

**Pipeline Configuration:**
- Add multiple stages to represent your release process
- Each stage can represent an environment or phase in your release process

## Pipeline Stages

### Stage Configuration

Each stage in your pipeline consists of:

1. **Stage Name**: A descriptive name for the stage (e.g., "Development", "Staging", "Production")
2. **Trigger**: When the stage should be activated
3. **Actions**: What should happen when the stage is triggered

### Stage Triggers

**On Enter** (`ON_ENTER`)
- Triggers immediately when a flag is added to this stage
- Use this for immediate actions when flags reach a particular stage

**Wait For** (`WAIT_FOR`)
- Triggers after waiting for a specified amount of time
- Configure the wait time in minutes, hours, or days
- Use this for gradual rollouts or testing periods

### Stage Actions

**Toggle Feature Actions:**
- **Enable flag for everyone**: Enables the feature flag for all users in the environment
- **Disable flag for everyone**: Disables the feature flag for all users in the environment
- **Enable flag for segment**: Enables the feature flag for a specific user segment
- **Disable flag for segment**: Disables the feature flag for a specific user segment

## Publishing a Release Pipeline

### Before Publishing

Before a release pipeline can be used, it must be published. Once published:
- The pipeline becomes active and can process feature flags
- The pipeline configuration becomes immutable
- You cannot modify stages, triggers, or actions

### Publishing Process

1. Complete your pipeline configuration
2. Review all stages, triggers, and actions
3. Click **Publish Pipeline**
4. Confirm the action when prompted

:::warning

Once published, a release pipeline cannot be modified. Ensure your configuration is correct before publishing.

:::

## Adding Flags to Release Pipelines

### From Feature Management

1. Navigate to your feature flags
2. Select the flag you want to add to a pipeline
3. Click the **Add to Release Pipeline** option
4. Select the pipeline and starting stage
5. Confirm the selection

### Pipeline Execution

Once a flag is added to a pipeline:
- It starts at the first stage you specified
- The pipeline automatically executes based on your configured triggers
- Actions are performed according to your stage configuration
- The flag progresses through each stage in sequence

## Managing Release Pipelines

### Viewing Pipeline Status

- **Active Pipelines**: View all published pipelines and their current status
- **Flag Progress**: Track which flags are currently in each stage

### Removing Flags from Pipelines

If you need to remove a flag from a pipeline:
1. Navigate to the flag or pipeline view
2. Select **Remove from Release Pipeline**
3. Confirm the action

