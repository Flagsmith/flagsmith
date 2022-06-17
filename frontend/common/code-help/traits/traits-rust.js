module.exports = (envId, { USER_ID }) => `use std::env;
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

let options = FlagsmithOptions {..Default::default()};
let flagsmith = Flagsmith::new(
    env::var("${envId}")
        .expect("FLAGSMITH_ENVIRONMENT_KEY not found in environment"),
    options,
);
// The method below triggers a network request
let identity_flags = flagsmith.get_identity_flags("${USER_ID}", Some(traits)).unwrap();
`;

// TODO: deal with the `Some(traits)` line above - this is invalid (I think)
