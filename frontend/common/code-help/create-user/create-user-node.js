import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_NODE_CLIENT, USER_ID, TRAIT_NAME },
  userId,
) => `import Flagsmith from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

const ${LIB_NAME} = new Flagsmith({${
  Constants.isCustomFlagsmithUrl()
    ? `\n    apiUrl: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
    environmentKey: '${envId}'
});

// Optional - set traits for this identity
const traitList = {"${TRAIT_NAME}": 42}

// Identify the user
const flags = await flagsmith.getIdentityFlags('${
  userId || USER_ID
}', traitList);

// get the state / value of the user's flags 
var isEnabled = flags.isFeatureEnabled('${FEATURE_NAME}');
var featureValue = flags.getFeatureValue('${FEATURE_NAME_ALT}');
`
