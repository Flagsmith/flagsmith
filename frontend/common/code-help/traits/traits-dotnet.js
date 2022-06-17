module.exports = (envId, { LIB_NAME, USER_ID, TRAIT_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `using Flagsmith;

static FlagsmithClient _flagsmithClient;
_flagsmithClient = new("${envId}");

var identifier = "delboy@trotterstraders.co.uk";
var traitKey = "car_type";
var traitValue = "robin_reliant";
var traitList = new List<Trait> { new Trait(traitKey, traitValue) };

# Sync
# The method below triggers a network request
var flags = _flagsmithClient.GetIdentityFlags(identifier, traitList).Result;
var showButton = flags.IsFeatureEnabled("secret_button").Result;

# Async
# The method below triggers a network request
var flags = await _flagsmithClient.GetIdentityFlags(identifier, traitList);
var showButton = await flags.IsFeatureEnabled("secret_button");
`;
