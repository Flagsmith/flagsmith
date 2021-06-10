module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `// This will create a user in the dashboard if they don't already exist
User user = new User();
user.setIdentifier("${userId || USER_ID}");

${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}.newBuilder()
    .setApiKey("${envId}")
    .build();

boolean featureEnabled = ${LIB_NAME}.hasFeatureFlag("${FEATURE_NAME}", user);
if (featureEnabled) {
    // Run the code to execute enabled feature
} else {
    // Run the code if feature switched off
}

String myRemoteConfig = ${LIB_NAME}.getFeatureFlagValue("${FEATURE_NAME_ALT}", user);
if (myRemoteConfig != null) {
    // Run the code to use remote config value
} else {
    // Run the code without remote config
}
`;
