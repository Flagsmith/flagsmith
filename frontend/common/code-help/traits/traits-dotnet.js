module.exports = (envId, { TRAIT_NAME }, userId) => `using Flagsmith;

FlagsmithClient _flagsmithClient;
_flagsmithClient = new("${envId}");

var traitList = new List<Trait> { new Trait(${TRAIT_NAME}, 42) };

# Identify a user, set their traits and retrieve the flags
var flags = _flagsmithClient.GetIdentityFlags(${userId}, traitList).Result;
`;
