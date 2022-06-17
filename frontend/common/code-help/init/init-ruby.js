module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

// Check for a feature
$is_enabled = $flags.is_feature_enabled('${FEATURE_NAME}')

// Or, use the value of a feature
$feature_value$flags.get_feature_value('${FEATURE_NAME_ALT}')
`;
