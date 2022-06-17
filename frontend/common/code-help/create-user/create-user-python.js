module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT, }, userId) => `from flagsmith import Flagsmith;

flagsmith = Flagsmith(environment_key="${envId}")

# Identify the user
identity_flags = flagsmith.get_identity_flags(identifier="${userId}", traits=traits)

# get the state / value of the user's flags
is_enabled = identity_flags.is_feature_enabled("${FEATURE_NAME}")
value = identity_flags.get_feature_value("${FEATURE_NAME_ALT}")
`;
