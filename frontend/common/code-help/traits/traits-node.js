import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, LIB_NAME, NPM_NODE_CLIENT, TRAIT_NAME, USER_ID },
  userId,
) => `import Flagsmith from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

const ${LIB_NAME} = new Flagsmith({${
  Constants.isCustomFlagsmithUrl() &&
  `\n    apiUrl: '${Constants.getFlagsmithSDKUrl()}',`
}
    environmentKey: '${envId}'
});
// Identify a user, set their traits and retrieve the flags
const traits = { ${TRAIT_NAME}: 'robin_reliant' };
const flags = await flagsmith.getIdentityFlags('${USER_ID}', traits);
`
