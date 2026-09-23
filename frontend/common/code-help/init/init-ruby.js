import Constants from 'common/constants'

export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: "${envId}"${
  Constants.isCustomFlagsmithUrl()
    ? `,\n    api_url: "${Constants.getFlagsmithSDKUrl()}"\n`
    : '\n'
})

# Load the environment's flags
$flags = $flagsmith.get_environment_flags

# Check whether the feature is enabled, or read its value
$is_enabled = $flags.is_feature_enabled('${FEATURE_NAME}')
$feature_value = $flags.get_feature_value('${FEATURE_NAME_ALT || FEATURE_NAME}')

puts "${FEATURE_NAME} enabled: #{$is_enabled}"
puts "${FEATURE_NAME_ALT || FEATURE_NAME} value: #{$feature_value}"
`
