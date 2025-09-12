import Constants from 'common/constants'

module.exports = (
  envId,
  { LIB_NAME, LIB_NAME_JAVA, TRAIT_NAME },
  userId,
) => `${LIB_NAME_JAVA} ${LIB_NAME} = ${LIB_NAME_JAVA}
.newBuilder()
.setApiKey("${envId}")${
  Constants.isCustomFlagsmithUrl() &&
  `\n    .withConfiguration(FlagsmithConfig.builder()
        .baseUri("${Constants.getFlagsmithSDKUrl()}")
        .build())`
}
.build();

Map<String, Object> traits = new HashMap<String, Object>();
traits.put("${TRAIT_NAME}", 42);

// Identify a user, set their traits and retrieve the flags 
Flags flags = flagsmith.getIdentityFlags("${userId}", traits);
`
