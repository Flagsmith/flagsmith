module.exports = (envId, { USER_ID }) => `
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};
use flagsmith_flag_engine::types::{FlagsmithValue, FlagsmithValueType};
use flagsmith_flag_engine::identities::Trait;

let options = FlagsmithOptions {..Default::default()};
let flagsmith = Flagsmith::new(
    "${envId}".to_string(),
    options,
);

let trait_key = "trait_key1";
let trait_value = "trai_value1";

let traits = vec![Trait {
    trait_key: trait_key.to_string(),
    trait_value: FlagsmithValue {
        value: trait_value.to_string(),
        value_type: FlagsmithValueType::String,
    },
}];
// The method below triggers a network request
let identity_flags = flagsmith.get_identity_flags("${USER_ID}", Some(traits)).unwrap();
`;

