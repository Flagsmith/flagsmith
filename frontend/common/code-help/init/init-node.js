module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_NAME_ALT, NPM_NODE_CLIENT }, customFeature) => `import ${LIB_NAME} from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

const ${LIB_NAME} = new Flagsmith({
    environmentKey: '${envId}'
});

const flags = await flagsmith.getEnvironmentFlags();

// Check for a feature
var isEnabled flags.isFeatureEnabled("${customFeature || FEATURE_NAME}")

// Or, use the value of a feature
var featureValue = flags.getFeatureValue('${customFeature || FEATURE_NAME_ALT}');
`;
