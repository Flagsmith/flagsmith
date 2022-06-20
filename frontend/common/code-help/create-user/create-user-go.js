module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `// The method below triggers a network request
flags, _ := client.GetIdentityFlags("${userId || USER_ID}", nil)

showButton, _ := flags.IsFeatureEnabled("${FEATURE_NAME}")
buttonData, _ := flags.GetFeatureValue("${FEATURE_NAME_ALT}")
`;
