module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `var testUser = bullettrain.User{Identifier: "${USER_ID}"}

c := bullettrain.DefaultClient("${envId}")

enabled, err := c.HasUserFeature(testUser, "${FEATURE_NAME}")

val, err := c.GetUserValue(testUser, ${FEATURE_NAME_ALT})

`;
