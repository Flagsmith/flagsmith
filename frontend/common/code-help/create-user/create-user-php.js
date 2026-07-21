import Constants from 'common/constants'

export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, USER_ID },
  userId,
) => `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}'${
  Constants.isCustomFlagsmithUrl() &&
  `,\n  '${Constants.getFlagsmithSDKUrl()}'\n`
});

// Identify the user
$flags = $flagsmith->getIdentityFlags('${userId}', $traits);

// get the state / value of the user's flags 
$isEnabled = $flags->isFeatureEnabled('${FEATURE_NAME}');
$featureValue = $flags->getFeatureValue('${FEATURE_NAME_ALT}');
`
