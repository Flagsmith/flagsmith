import Constants from 'common/constants'

module.exports = (envId, { FEATURE_NAME, FEATURE_NAME_ALT }) => `
use flagsmith::{Flag, Flagsmith, FlagsmithOptions};

let options = FlagsmithOptions {${
  Constants.isCustomFlagsmithUrl &&
  `api_url: "${Constants.getFlagsmithSDKUrl()}".to_string(),\n`
}..Default::default()};
let flagsmith = Flagsmith::new(
    "${envId}".to_string(),
    options,
);

// The method below triggers a network request
let flags = flagsmith.get_environment_flags().unwrap();

// Check for a feature
let show_button = flags.is_feature_enabled("${FEATURE_NAME}").unwrap();

let button_data = flags.get_feature_value_as_string("${FEATURE_NAME_ALT}").unwrap();
`
