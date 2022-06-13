module.exports = (envId, { LIB_NAME, USER_ID, TRAIT_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `
// Set a user trait
Trait userTrait = await BulletTrainClient.instance.SetTrait("${USER_ID}", "${TRAIT_NAME}", "blue");

Identity userIdentity = await BulletTrainClient.instance.GetUserIdentity("${USER_ID}");
if (userIdentity != null) {
  // Run the code to use user identity i.e. userIdentity.flags or userIdentity.traits
}
`;
