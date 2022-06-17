module.exports = (envId, {
    FEATURE_NAME,
    FEATURE_FUNCTION,
    FEATURE_NAME_ALT
}) => `fs := flagsmith.DefaultClient("${envId}")
// Check for a feature
enabled, err := fs.FeatureEnabled("${FEATURE_NAME}")
if err != nil {
    log.Fatal(err)
} else {
    if (enabled) {
        ${FEATURE_FUNCTION}()
    }
}

// Or, use the value of a feature
feature_value, err := fs.GetValue("${FEATURE_NAME_ALT}")
if err != nil {
    log.Fatal(err)
} else {
    fmt.Printf(feature_value)
}
`;

// TODO
