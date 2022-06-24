module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

// Identify the user
$flags = $flagsmith.get_identity_flags('${userId}')

// get the state / value of the user's flags
$is_enabled = $flags.is_feature_enabled('${FEATURE_NAME}')
$feature_value = $flags.get_feature_value('${FEATURE_NAME_ALT}')
`;
