module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }, customFeature) => `using Flagsmith;

static FlagsmithClient _flagsmithClient;

_flagsmithClient = new("${envId}");

var flags = await _flagsmithClient.GetEnvironmentFlags();  # This method triggers a network request

// Check for a feature
var isEnabled = await flags.IsFeatureEnabled("${customFeature || FEATURE_NAME}");

// Or, use the value of a feature
var featureValue = await flags.GetFeatureValue("${customFeature || FEATURE_NAME_ALT}");
`;
