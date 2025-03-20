import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, USER_ID, TRAIT_NAME },
  userId,
) => `from flagsmith import Flagsmith

flagsmith = Flagsmith(environment_key="${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `, api_url="${Constants.getFlagsmithSDKUrl()}"`
    : ''
})

# Optional - set traits for this identity
traits = {"${TRAIT_NAME}": 42}

# Identify the user
identity_flags = flagsmith.get_identity_flags(identifier="${
  userId || USER_ID
}", traits=traits)

# get the state / value of the user's flags
is_enabled = identity_flags.is_feature_enabled("${FEATURE_NAME}")
feature_value = identity_flags.get_feature_value("${FEATURE_NAME_ALT}")
`
