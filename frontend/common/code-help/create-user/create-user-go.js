module.exports = (envId, { USER_ID, FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `// The method below triggers a network request
flags, _ := client.GetIdentityFlags("${userId || USER_ID}", nil)

isEnabled, _ := flags.IsFeatureEnabled("${FEATURE_NAME}")
featureValue, _ := flags.GetFeatureValue("${FEATURE_NAME_ALT}")
`;
