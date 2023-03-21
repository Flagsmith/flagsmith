module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, USER_ID },
  userId,
) => `// The method below triggers a network request
flags, _ := client.GetIdentityFlags("${userId || USER_ID}", nil)

isEnabled, _ := flags.IsFeatureEnabled("${FEATURE_NAME}")
featureValue, _ := flags.GetFeatureValue("${FEATURE_NAME_ALT}")
`
