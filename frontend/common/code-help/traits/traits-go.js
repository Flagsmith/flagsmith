module.exports = (envId, { TRAIT_NAME }, userId) => `trait := flagsmith.Trait{TraitKey: "trait", TraitValue: "trait_value"}
traits = []*flagsmith.Trait{&trait}

// The method below triggers a network request
flags, _ := client.GetIdentityFlags("${userId || USER_ID}", traits)

showButton, _ := flags.IsFeatureEnabled("${FEATURE_NAME}")
buttonData, _ := flags.GetFeatureValue("${FEATURE_NAME_ALT}")
`;
