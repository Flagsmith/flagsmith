import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_NODE_CLIENT },
  customFeature,
) => `import Flagsmith from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

const ${LIB_NAME} = new Flagsmith({${
  Constants.isCustomFlagsmithUrl &&
  `\n    apiUrl: '${Project.flagsmithClientAPI}',`
}
    environmentKey: '${envId}'
});

const flags = await flagsmith.getEnvironmentFlags();

// Check for a feature
var isEnabled = flags.isFeatureEnabled("${customFeature || FEATURE_NAME}")

// Or, use the value of a feature
var featureValue = flags.getFeatureValue('${
  customFeature || FEATURE_NAME_ALT
}');
`
