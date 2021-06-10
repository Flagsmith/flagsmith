import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `let bt = bullettrain::Client::new("${envId}");

// Check for a feature
if bt.feature_enabled("${FEATURE_NAME}")? {
    println!("Feature enabled");
}

// Or, use the value of a feature
if let Some(Value::String(s)) = bt.get_value("${FEATURE_NAME_ALT}")? {
    println!("{}", s);
}

`;
