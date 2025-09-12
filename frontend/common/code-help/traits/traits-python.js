import Constants from 'common/constants'

module.exports = (
  envId,
  { TRAIT_NAME },
  userId,
) => `from flagsmith import Flagsmith

flagsmith = Flagsmith(environment_key="${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `, api_url="${Constants.getFlagsmithSDKUrl()}"`
    : ''
})

traits = {"${TRAIT_NAME}": 42}

# Identify a user, set their traits and retrieve the flags
identity_flags = flagsmith.get_identity_flags(identifier="${userId}", traits=traits)
`
