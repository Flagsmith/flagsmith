import Constants from 'common/constants'

// FlagsmithClient takes a FlagsmithConfiguration, not an environment key, and
// top-level statements reject `static` on a declaration (error CS0106).
export default (envId, { FEATURE_NAME, FEATURE_NAME_ALT }) => `using Flagsmith;

var flagsmithClient = new FlagsmithClient(new FlagsmithConfiguration
{
    EnvironmentKey = "${envId}",${
  Constants.isCustomFlagsmithUrl()
    ? `\n    ApiUri = new Uri("${Constants.getFlagsmithSDKUrl()}"),`
    : ''
}
});

// The method below triggers a network request
var flags = await flagsmithClient.GetEnvironmentFlags();

// Check whether the feature is enabled, or read its value
var isEnabled = await flags.IsFeatureEnabled("${FEATURE_NAME}");
var featureValue = await flags.GetFeatureValue("${
  FEATURE_NAME_ALT || FEATURE_NAME
}");

Console.WriteLine($"${FEATURE_NAME} enabled: {isEnabled}");
Console.WriteLine($"${FEATURE_NAME_ALT || FEATURE_NAME} value: {featureValue}");
`
