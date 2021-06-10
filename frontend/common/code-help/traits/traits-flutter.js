module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, TRAIT_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `final user = FeatureUser(identifier: '${USER_ID}');

final userTrait = await flagsmithClient.getTrait(user, '${TRAIT_NAME}');
if (userTrait != null) {
    // run the code to use user trait
} else {
    // run the code without user trait
}

// Or get specific traits 
final userTraits = await flagsmithClient.getTraits(user, keys: ['${TRAIT_NAME}', 'other_trait']);

// Or get all traits
final userTraits = await flagsmithClient.getTraits(user)

`;
