module.exports = (envId, { LIB_NAME, USER_ID, TRAIT_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}
.newBuilder()
.setApiKey("${envId}")
.build();

// This will create a user in the dashboard if they don't already exist
String identifier = "delboy@trotterstraders.co.uk"
Map<String, Object> traits = new HashMap<String, Object>();
traits.put("car_type", "robin_reliant");

// The method below triggers a network request
Flags flags = flagsmith.getIdentityFlags(identifier, traits);
Boolean showButton = flags.isFeatureEnabled(featureName);
Object value = flags.getFeatureValue(featureName);
`;
