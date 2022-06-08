import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `//In your application, initialise the Flagsmith client with your API key:

final flagsmithClient = FlagsmithClient(
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

await flagsmithClient.getFeatureFlags(reload: true) // fetch updates from api

// Check for a feature
bool ${FEATURE_NAME} = await flagsmithClient.hasFeatureFlag("${FEATURE_NAME}");

// Or, use the value of a feature
final ${FEATURE_NAME_ALT} = await flagsmithClient.getFeatureFlagValue("${FEATURE_NAME_ALT}");
`;
