import Constants from 'common/constants'
module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, LIB_NAME_JAVA },
  customFeature,
) => `${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}
    .newBuilder()
    .setApiKey("${envId}")${
  Constants.isCustomFlagsmithUrl()
    ? `\n    .withConfiguration(FlagsmithConfig.newBuilder()
        .baseUri("${Constants.getFlagsmithSDKUrl()}")
        .build())`
    : ''
}
    .build();

Flags flags = flagsmith.getEnvironmentFlags();

// Check for a feature
boolean isEnabled = flags.isFeatureEnabled("${customFeature || FEATURE_NAME}");

// Or, use the value of a feature
Object featureValue = flags.getFeatureValue("${
  customFeature || FEATURE_NAME_ALT
}");
`
