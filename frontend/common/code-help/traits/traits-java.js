module.exports = (envId, { LIB_NAME, TRAIT_NAME, LIB_NAME_JAVA }, userId) => `${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}
.newBuilder()
.setApiKey("${envId}")
.build();

Map<String, Object> traits = new HashMap<String, Object>();
traits.put("${TRAIT_NAME}", 42);

// Identify a user, set their traits and retrieve the flags 
Flags flags = flagsmith.getIdentityFlags("${userId}", traits);
`;
