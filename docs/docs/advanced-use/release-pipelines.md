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
- **Description**: Optional description to explain the pipeline's purpose

**Pipeline Configuration:**
- Add multiple stages to represent your release process
- Each stage can represent an environment or phase in your release process
- Stages are executed in order from first to last

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

**Feature Value Actions:**
- **Update feature value**: Changes the remote config value for all users
- **Update feature value for segment**: Changes the remote config value for a specific segment

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
- **Execution History**: Review past pipeline executions and their outcomes

### Removing Flags from Pipelines

If you need to remove a flag from a pipeline:
1. Navigate to the flag or pipeline view
2. Select **Remove from Release Pipeline**
3. Confirm the action

:::info

Removing a flag from a pipeline stops its automated progression but doesn't affect the flag's current state in your environments.

:::

## Best Practices

### Pipeline Design

- **Keep It Simple**: Start with a basic pipeline and add complexity as needed
- **Environment Alignment**: Align pipeline stages with your actual environments
- **Consistent Naming**: Use clear, consistent naming conventions for stages

### Timing Considerations

- **Allow Testing Time**: Build in sufficient wait times for testing between stages
- **Consider Time Zones**: Account for team availability when setting trigger times
- **Monitor Progress**: Regularly review pipeline execution to ensure it meets your needs

### Risk Management

- **Test Thoroughly**: Ensure your pipeline configuration is tested before publishing
- **Segment First**: Consider using segments before enabling for all users
- **Have Rollback Plans**: Maintain the ability to manually override pipeline actions if needed

## Common Use Cases

### Progressive Rollout

Create a pipeline that gradually enables features:
1. **Development**: Enable for internal testing
2. **Staging**: Enable for QA team (wait 24 hours)
3. **Production Beta**: Enable for beta user segment (wait 48 hours)  
4. **Production**: Enable for all users

### Scheduled Releases

Automate feature releases at specific times:
1. **Preparation**: Stage the feature (ready state)
2. **Launch**: Wait until launch time, then enable for all users
3. **Post-Launch**: Monitor and adjust based on feedback

### A/B Testing Pipeline

Manage A/B test progression:
1. **Test Setup**: Configure test parameters
2. **Limited Test**: Enable for small user segment
3. **Expanded Test**: Wait for statistical significance, then expand
4. **Winner Selection**: Automatically implement winning variant

## Troubleshooting

### Common Issues

**Pipeline Not Executing**
- Verify the pipeline is published
- Check that flags are properly added to the pipeline
- Review trigger configurations

**Unexpected Behavior**
- Ensure segment configurations are correct
- Verify environment permissions
- Check for conflicting manual flag changes

**Timing Issues**
- Review wait time configurations
- Consider timezone differences
- Check for system delays or outages

### Getting Help

If you encounter issues with release pipelines:
- Review the audit logs for pipeline execution details
- Check the pipeline status dashboard
- Contact support with specific pipeline and flag information

## Limitations

- Maximum of 30 stages per pipeline
- Once published, pipelines cannot be modified
- Pipeline execution requires appropriate environment permissions
- Some actions may have slight delays due to system processing 