import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `from flagsmith import Flagsmith;

flagsmith = Flagsmith(environment_id="${envId}")

# This will create a user in the dashboard if they don't already exist
# Check for a feature
if flagsmith.has_feature("${FEATURE_NAME}"):
  if flagsmith.feature_enabled("${FEATURE_NAME}"):
    # Show my awesome cool new feature to the world

# Or, use the value of a feature
value = flagsmith.get_value("${FEATURE_NAME_ALT}")
`;
