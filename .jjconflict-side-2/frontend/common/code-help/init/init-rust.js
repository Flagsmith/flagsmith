import Constants from 'common/constants'

export default (envId, { FEATURE_NAME, FEATURE_NAME_ALT }) => `
use flagsmith::{Flagsmith, FlagsmithOptions};

${
  // rustfmt splits a struct literal that doesn't fit on one line, and the API
  // URL makes this one long.
  Constants.isCustomFlagsmithUrl()
    ? `let options = FlagsmithOptions {
    api_url: "${Constants.getFlagsmithSDKUrl()}".to_string(),
    ..Default::default()
};`
    : `let options = FlagsmithOptions { ..Default::default() };`
}
let flagsmith = Flagsmith::new(
    "${envId}".to_string(),
    options,
);

// The method below triggers a network request
let flags = flagsmith.get_environment_flags().unwrap();

// Check whether the feature is enabled, or read its value
let is_enabled = flags.is_feature_enabled("${FEATURE_NAME}").unwrap();
let feature_value = flags.get_feature_value_as_string("${
  FEATURE_NAME_ALT || FEATURE_NAME
}").unwrap();
println!("${FEATURE_NAME} enabled: {}", is_enabled);
println!("${FEATURE_NAME_ALT || FEATURE_NAME} value: {}", feature_value);
`
