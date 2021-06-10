import Utils from '../../utils/utils';

module.exports = (envId, {
    FEATURE_NAME,
    FEATURE_FUNCTION,
    FEATURE_NAME_ALT
}) => `bt := bullettrain.DefaultClient("${envId}")
// Check for a feature
enabled, err := bt.FeatureEnabled("${FEATURE_NAME}")
if err != nil {
    log.Fatal(err)
} else {
    if (enabled) {
        ${FEATURE_FUNCTION}()
    }
}

// Or, use the value of a feature
feature_value, err := bt.GetValue("${FEATURE_NAME_ALT}")
if err != nil {
    log.Fatal(err)
} else {
    fmt.Printf(feature_value)
}
`;