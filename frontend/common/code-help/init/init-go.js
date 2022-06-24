module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }, customFeature) => `
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Initialise the Flagsmith client
client := flagsmith.NewClient('${envId}', flagsmith.WithContext(ctx))

// The method below triggers a network request
flags, _ := client.GetEnvironmentFlags()
isEnabled, _ := flags.IsFeatureEnabled("${customFeature || FEATURE_NAME}")
featureValue, _ := flags.GetFeatureValue("${customFeature || FEATURE_NAME_ALT}")
`;
