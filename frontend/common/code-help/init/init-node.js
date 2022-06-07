module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_NODE_CLIENT, NPM_CLIENT }, customFeature) => `import ${LIB_NAME} from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

const ${LIB_NAME} = new Flagsmith({'${envId}'});

const flags = await flagsmith.getEnvironmentFlags();

// Check for a feature
var showButton flags.isFeatureEnabled("${customFeature || FEATURE_NAME}")

// Or, use the value of a feature
var buttonData = flags.getFeatureValue('${customFeature || FEATURE_NAME_ALT}');
`;
