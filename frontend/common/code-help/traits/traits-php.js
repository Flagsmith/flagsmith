module.exports = (envId, { LIB_NAME, USER_ID, LIB_NAME_JAVA, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}');

// This will create a user in the dashboard if they don't already exist
$identifier = 'delboy@trotterstraders.co.uk';
$traits = (object) [ 'car_type' => 'robin_reliant' ];

$flags = $flagsmith->getIdentityFlags($identifier, $traits);
$showButton = $flags->isFeatureEnabled('secret_button');
$buttonData = $flags->getFeatureValue('secret_button');
`;
