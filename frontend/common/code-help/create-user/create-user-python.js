module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `from flagsmith import Flagsmith;

flagsmith = Flagsmith(
    environment_key = os.environ.get("${envId}")
)

# This will create a user in the dashboard if they don't already exist
identifier = "delboy@trotterstraders.co.uk"
traits = {"car_type": "robin_reliant"}

# The method below triggers a network request
identity_flags = flagsmith.get_identity_flags(identifier=identifier, traits=traits)

# Check for a feature
show_button = identity_flags.is_feature_enabled("secret_button")

# Or, use the value of a feature
button_data = json.loads(identity_flags.get_feature_value("secret_button"))
`;
