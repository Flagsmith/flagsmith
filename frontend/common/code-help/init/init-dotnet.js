module.exports = (envId, { LIB_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `using Flagsmith;

static FlagsmithClient _flagsmithClient;

_flagsmithClient = new("${envId}");

var flags = _flagsmithClient.GetEnvironmentFlags();  # This method triggers a network request

// Check for a feature
var featureEnabled = flags.IsFeatureEnabled("${customFeature || FEATURE_NAME}");

// Or, use the value of a feature
var myRemoteConfig = flags.GetFeatureValue("${customFeature || FEATURE_NAME_ALT}").Result;
`;
