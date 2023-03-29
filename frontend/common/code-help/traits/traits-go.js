module.exports = (
  envId,
  { TRAIT_NAME, USER_ID },
  userId,
) => `trait := flagsmith.Trait{TraitKey: "${TRAIT_NAME}", TraitValue: "42"}
traits = []*flagsmith.Trait{&trait}

// Identify a user, set their traits and retrieve the flags
flags, _ := client.GetIdentityFlags("${userId || USER_ID}", traits)
`
