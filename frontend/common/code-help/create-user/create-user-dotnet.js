module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `BulletTrainConfiguration configuration = new BulletTrainConfiguration()
{
    ApiUrl = "https://api.flagsmith.com/api/v1/",
    EnvironmentKey = "${envId}"
};

// This will create a user in the dashboard if they don't already exist
BulletTrainClient bulletClient = new BulletTrainClient(configuration);

bool featureEnabled = await BulletTrainClient.instance
    .HasFeatureFlag("${FEATURE_NAME}", "${USER_ID}");
    
string myRemoteConfig = await BulletTrainClient.instance
    .GetFeatureValue("${FEATURE_NAME_ALT}", "${USER_ID}");

`;
