import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

// Check for a feature
$show_button = $flags.is_feature_enabled('${FEATURE_NAME}')

// Or, use the value of a feature]
$button_data = $flags.get_feature_value('${FEATURE_NAME_ALT}')
`;
