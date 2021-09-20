module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `use Flagsmith\\Flagsmith;

$bt = new Flagsmith('${envId}');

// This will create a user in the dashboard if they don't already exist

// Check for a feature
$${FEATURE_NAME} = $bt->featureEnabled("${FEATURE_NAME}","${USER_ID}");

// Or, use the value of a feature
$${FEATURE_NAME_ALT} = $bt->getValue("${FEATURE_NAME_ALT}","${USER_ID}");
`;
