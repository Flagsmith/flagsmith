module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

// This will create a user in the dashboard if they don't already exist.
$flags = $flagsmith.get_environment_flags()

// Check for a feature
$show_button = $flags.is_feature_enabled('secret_button')

// Or, use the value of a feature
$button_data = $flags.get_feature_value('secret_button')
`;
