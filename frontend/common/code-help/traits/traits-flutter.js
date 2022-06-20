module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, TRAIT_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `final flagsmithClient = FlagsmithClient(
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

// An identifier is created when we get the feature flags for said identifier for the first time
flagsmithClient.getFeatureFlags(user: const Identity(identifier: '${USER_ID}'));
// Create a new user trait based on the above identifier
flagsmithClient.createTrait(
    value: TraitWithIdentity(
    identity: const Identity(identifier: '${USER_ID}'),
    key: 'age',
    value: '21',
    ),
);

// Update the previously created trait with a new value
flagsmithClient.updateTraits(value: [
    TraitWithIdentity(
    identity: const Identity(identifier: '${USER_ID}'),
    key: 'age',
    value: '20',
    ),
]);

final user = FeatureUser(identifier: '');
// This will create a user in the dashboard if they don't already exist
bool featureEnabled = await flagsmithClient.hasFeatureFlag('${FEATURE_NAME}', user: const Identity(identifier: '${USER_ID}'));

final myRemoteConfig = await flagsmithClient.getFeatureFlagValue('${FEATURE_NAME_ALT}', user: const Identity(identifier: '${USER_ID}'));
`;
