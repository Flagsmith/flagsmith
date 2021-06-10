module.exports = (envId, { LIB_NAME, USER_ID, TRAIT_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `FeatureUser user = new FeatureUser();
user.setIdentifier("${USER_ID}");

flagsmithClient.identifyUserWithTraits(FeatureUser user, Arrays.asList(
    trait(null, "${TRAIT_NAME}", "21")
));

// Or to update a trait given context
Trait userTrait = flagsmithClient.getTrait(user, "${TRAIT_NAME}");
if (userTrait != null) {    
    // update the value for a user trait
    userTrait.setValue("21");
    Trait updated = flagsmithClient.updateTrait(user, userTrait);
} else {
    // run the code that doesn't depend on the user trait
}

List<Trait> userTraits = flagsmithClient.getTraits(user, "${TRAIT_NAME}", "other_trait");
if (userTraits != null) {    
    // run the code that uses the user traits
} else {
    // run the code doesn't depend on user traits
}


`;
