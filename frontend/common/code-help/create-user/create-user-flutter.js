import Constants from 'common/constants'
module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, USER_ID },
  userId,
) => `final flagsmithClient = FlagsmithClient(
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

// This will create a user in the dashboard if they don't already exist
final user = Identity(identifier: '${userId || USER_ID}');

bool featureEnabled = await flagsmithClient
  .hasFeatureFlag('${FEATURE_NAME}', user: user);
  
final myRemoteConfig = await flagsmithClient
  .getFeatureFlagValue('${FEATURE_NAME_ALT}', user: user);

`
