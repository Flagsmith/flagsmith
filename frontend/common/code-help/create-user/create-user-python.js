module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `from flagsmith import Flagsmith

flagsmith = Flagsmith(environment_id="${envId}")

# This will create a user in the dashboard if they don't already exist

# Check for a feature
if flagsmith.has_feature("${FEATURE_NAME}", '${USER_ID}'):
  if flagsmith.feature_enabled("${FEATURE_NAME}"):
    # Show my awesome cool new feature to the world

# Or, use the value of a feature
value = flagsmith.get_value("${FEATURE_NAME_ALT}", "${USER_ID}")

`;
