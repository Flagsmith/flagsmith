module.exports = (envId, { LIB_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}.newBuilder()
    .setApiKey("${envId}")
    .build();

// Check for a feature
boolean featureEnabled = ${LIB_NAME}.hasFeatureFlag("${customFeature || FEATURE_NAME}");

// Or, use the value of a feature
String myRemoteConfig = ${LIB_NAME}.getFeatureFlagValue("${customFeature || FEATURE_NAME_ALT}");

`;
