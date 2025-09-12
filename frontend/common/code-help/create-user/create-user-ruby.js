import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, USER_ID },
  userId,
) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key="${envId}"${
  Constants.isCustomFlagsmithUrl() &&
  `,\n    api_url="${Constants.getFlagsmithSDKUrl()}"\n`
})

// Identify the user
$flags = $flagsmith.get_identity_flags('${userId || USER_ID}')

// get the state / value of the user's flags
$is_enabled = $flags.is_feature_enabled('${FEATURE_NAME}')
$feature_value = $flags.get_feature_value('${FEATURE_NAME_ALT}')
`
