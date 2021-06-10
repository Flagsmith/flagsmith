import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `require "flagsmith"

flagsmith = Flagsmith.new("${envId}")

// Check for a feature
if flagsmith.feature_enabled?("${FEATURE_NAME}")
end

// Or, use the value of a feature
if flagsmith.get_value("${FEATURE_NAME_ALT}")
end`;
