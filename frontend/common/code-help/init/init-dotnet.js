module.exports = (envId, { LIB_NAME, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `BulletTrainConfiguration configuration = new BulletTrainConfiguration()
{
    ApiUrl = "https://api.flagsmith.com/api/v1/",
    EnvironmentKey = "${envId}"
};

BulletTrainClient bulletClient = new BulletTrainClient(configuration);
// Check for a feature
bool featureEnabled = await ${LIB_NAME}.HasFeatureFlag("${customFeature || FEATURE_NAME}");

// Or, use the value of a feature
string myRemoteConfig = await ${LIB_NAME}.GetFeatureValue("${customFeature || FEATURE_NAME_ALT}");

`;
