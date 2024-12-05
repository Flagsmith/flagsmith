import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `from flagsmith import Flagsmith

flagsmith = Flagsmith(\n    environment_key="${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `,\n    api_url="${Constants.getFlagsmithSDKUrl()}",\n`
    : ','
})

# The method below triggers a network request
flags = flagsmith.get_environment_flags()

# Check for a feature
is_enabled = flags.is_feature_enabled("${FEATURE_NAME}")

# Or, use the value of a feature
feature_value = json.loads(flags.get_feature_value("${FEATURE_NAME_ALT}"))
`
