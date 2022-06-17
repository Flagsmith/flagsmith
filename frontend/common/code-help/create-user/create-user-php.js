module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}');

// Identify the user
$flags = $flagsmith->getIdentityFlags('${userId}', $traits);

// get the state / value of the user's flags 
$isEnabled = $flags->isFeatureEnabled('${FEATURE_NAME}');
$featureValue$flags->getFeatureValue('${FEATURE_NAME_ALT}');
`;
