module.exports = (envId, { TRAIT_NAME }, userId) => `client := flagsmith.DefaultClient("${envId}")

trait := flagsmith.Trait{TraitKey: "${TRAIT_NAME}", TraitValue: "trait_value"}
traits = []*flagsmith.Trait{&trait}

// Identify a user, set their traits and retrieve the flags
flags, _ := client.GetIdentityFlags("${userId}", traits)
`;
