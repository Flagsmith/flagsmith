import Constants from 'common/constants'

export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `from flagsmith import Flagsmith

flagsmith = Flagsmith(\n    environment_key="${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `,\n    api_url="${Constants.getFlagsmithSDKUrl()}",\n`
    : ',\n'
})

# The method below triggers a network request
flags = flagsmith.get_environment_flags()

# Check whether the feature is enabled
is_enabled = flags.is_feature_enabled("${FEATURE_NAME}")
print("${FEATURE_NAME} enabled:", is_enabled)

# Or read its value
feature_value = flags.get_feature_value("${FEATURE_NAME_ALT || FEATURE_NAME}")
print("${FEATURE_NAME_ALT || FEATURE_NAME} value:", feature_value)
`
