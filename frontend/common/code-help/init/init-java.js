import Constants from 'common/constants'
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, LIB_NAME_JAVA },
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

// The method below triggers a network request
Flags flags = ${LIB_NAME}.getEnvironmentFlags();

// Check whether the feature is enabled, or read its value
boolean isEnabled = flags.isFeatureEnabled("${FEATURE_NAME}");
Object featureValue = flags.getFeatureValue("${
  FEATURE_NAME_ALT || FEATURE_NAME
}");
`
