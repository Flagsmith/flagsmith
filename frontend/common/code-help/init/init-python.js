import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `from flagsmith import Flagsmith;

flagsmith = Flagsmith(
    environment_key = os.environ.get("${envId}")
)

# The method below triggers a network request
flags = flagsmith.get_environment_flags()

# Check for a feature
show_button = flags.is_feature_enabled("${FEATURE_NAME}")

# Or, use the value of a feature
button_data = json.loads(flags.get_feature_value("${FEATURE_NAME_ALT}"))
`;
