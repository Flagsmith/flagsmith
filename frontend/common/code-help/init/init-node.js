import Constants from 'common/constants'

export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_NODE_CLIENT },
) => `import { Flagsmith } from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

const ${LIB_NAME} = new Flagsmith({${
  Constants.isCustomFlagsmithUrl()
    ? `\n    apiUrl: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
    environmentKey: '${envId}'
});

// The method below triggers a network request
const flags = await ${LIB_NAME}.getEnvironmentFlags();

// Check whether the feature is enabled, or read its value
const isEnabled = flags.isFeatureEnabled("${FEATURE_NAME}");
const featureValue = flags.getFeatureValue("${
  FEATURE_NAME_ALT || FEATURE_NAME
}");
console.log("${FEATURE_NAME} enabled:", isEnabled);
console.log("${FEATURE_NAME_ALT || FEATURE_NAME} value:", featureValue);
`
