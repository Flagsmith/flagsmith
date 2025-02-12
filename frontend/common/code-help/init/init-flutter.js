import Constants from 'common/constants'
module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `//In your application, initialise the Flagsmith client with your API key:

final flagsmithClient = FlagsmithClient(
        apiKey: '${envId}',${
  Constants.isCustomFlagsmithUrl()
    ? `\n        baseURI: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
        config: config,
        seeds: <Flag>[
            Flag.seed('feature', enabled: true),
        ],
    );

//if you prefer async initialization then you should use
//final flagsmithClient = await FlagsmithClient.init(
//        apiKey: '${envId}',${
  Constants.isCustomFlagsmithUrl()
    ? `\n//        baseURI: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
//        config: config,
//        seeds: <Flag>[
//            Flag.seed('feature', enabled: true),
//        ],
//        update: false,
//    );

await flagsmithClient.getFeatureFlags(reload: true) // fetch updates from api

// Check for a feature
bool ${FEATURE_NAME} = await flagsmithClient.hasFeatureFlag("${FEATURE_NAME}");

// Or, use the value of a feature
final ${FEATURE_NAME_ALT} = await flagsmithClient.getFeatureFlagValue("${FEATURE_NAME_ALT}");
`
