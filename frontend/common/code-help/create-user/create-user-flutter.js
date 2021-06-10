module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `final flagsmithClient = FlagsmithClient(
        apiKey: '${envId}' 
        config: config, 
        seeds: <Flag>[
            Flag.seed('feature', enabled: true),
        ],
    );

//if you prefer async initialization then you should use
//final flagsmithClient = await FlagsmithClient.init(
//        apiKey: 'YOUR_ENV_API_KEY',
//        config: config, 
//        seeds: <Flag>[
//            Flag.seed('feature', enabled: true),
//        ], 
//        update: false,
//    );

// This will create a user in the dashboard if they don't already exist
final user = FeatureUser(identifier: '${USER_ID}');

bool featureEnabled = await flagsmithClient
  .hasFeatureFlag('${FEATURE_NAME}', user: user);
  
final myRemoteConfig = await flagsmithClient
  .getFeatureFlagValue('${FEATURE_NAME_ALT}', user: user);

`;
