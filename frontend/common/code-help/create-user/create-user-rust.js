module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `use std::env;
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

let options = FlagsmithOptions {..Default::default()};
let flagsmith = Flagsmith::new(
    env::var("${envId}")
        .expect("FLAGSMITH_ENVIRONMENT_KEY not found in environment"),
    options,
);

// Identify the user
let identity_flags = flagsmith.get_identity_flags("${userId}").unwrap();

// get the state / value of the user's flags 
let is_enabled = identity_flags.is_feature_enabled("${FEATURE_NAME}").unwrap();
let feature_value = identity_flags.get_feature_value_as_string("${FEATURE_NAME_ALT}").unwrap();
`;

// TODO: verify that get_identity_flags works without traits

