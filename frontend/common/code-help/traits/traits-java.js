module.exports = (envId, { LIB_NAME, USER_ID, TRAIT_NAME, LIB_NAME_JAVA, FEATURE_NAME }) => `${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}
.newBuilder()
.setApiKey("${envId}")
.build();

Map<String, Object> traits = new HashMap<String, Object>();
traits.put("${TRAIT_NAME}", 42);

// The method below triggers a network request and creates a user in the dashboard if they don't exist alreadt
Flags flags = flagsmith.getIdentityFlags(${USER_ID}, traits);
Boolean showButton = flags.isFeatureEnabled(${FEATURE_NAME});
Object value = flags.getFeatureValue(${FEATURE_NAME});
`;
