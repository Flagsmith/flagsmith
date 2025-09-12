import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
  customFeature,
) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: "${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `,\n    api_url: "${Constants.getFlagsmithSDKUrl()}"\n`
    : '\n'
})

// Load the environment's flags locally
$flags = $flagsmith.get_environment_flags

// Check for a feature
$is_enabled = $flags.is_feature_enabled('${customFeature || FEATURE_NAME}')

// Or, use the value of a feature
$feature_value = $flags.get_feature_value('${
  customFeature || FEATURE_NAME_ALT
}')
`
