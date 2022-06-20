module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

let options = FlagsmithOptions {..Default::default()};
let flagsmith = Flagsmith::new(
    "${envId}".to_string(),
    options,
);

// Identify the user
let identity_flags = flagsmith.get_identity_flags("${userId}", None).unwrap();

// get the state / value of the user's flags
let is_enabled = identity_flags.is_feature_enabled("${FEATURE_NAME}").unwrap();
let feature_value = identity_flags.get_feature_value_as_string("${FEATURE_NAME_ALT}").unwrap();
`;

