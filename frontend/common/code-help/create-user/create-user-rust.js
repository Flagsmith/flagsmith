import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `use std::env;
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

let options = FlagsmithOptions {..Default::default()};
let flagsmith = Flagsmith::new(
    env::var("${envId}")
        .expect("FLAGSMITH_ENVIRONMENT_KEY not found in environment"),
    options,
);
// The method below triggers a network request
let identity_flags = flagsmith.get_identity_flags(identifier, Some(traits)).unwrap();

// Check for a feature
let show_button = identity_flags.is_feature_enabled("secret_button").unwrap();

// Or, use the value of a feature
let button_data = identity_flags.get_feature_value_as_string("secret_button").unwrap();
`;
