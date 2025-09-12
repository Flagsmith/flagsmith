import Constants from 'common/constants'
module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}'${
  Constants.isCustomFlagsmithUrl()
    ? `, '${Constants.getFlagsmithSDKUrl()}'`
    : ''
});

// Check for a feature
$${FEATURE_NAME} = $flags->isFeatureEnabled('${FEATURE_NAME}');

// Or use the value of a feature
$${FEATURE_NAME_ALT} = $flags->getFeatureValue('${FEATURE_NAME_ALT}')
`
