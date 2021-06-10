module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `require "flagsmith"

flagsmith = Flagsmith.new("${envId}")

// This will create a user in the dashboard if they don't already exist.

// Check for a feature
if flagsmith.feature_enabled?("${FEATURE_NAME}","${USER_ID}")
end

// Or, use the value of a feature
if flagsmith.get_value("${FEATURE_NAME_ALT}","${USER_ID}")
end`;
