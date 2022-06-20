module.exports = (envId, {
    FEATURE_NAME,
    FEATURE_FUNCTION,
    FEATURE_NAME_ALT
}) => `ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Initialise the Flagsmith client
client := flagsmith.NewClient('${envId}', flagsmith.WithContext(ctx))

// The method below triggers a network request
flags, _ := client.GetEnvironmentFlags()
showButton, _ := flags.IsFeatureEnabled("${FEATURE_NAME}")
buttonData, _ := flags.GetFeatureValue("${FEATURE_NAME_ALT}")
`;
