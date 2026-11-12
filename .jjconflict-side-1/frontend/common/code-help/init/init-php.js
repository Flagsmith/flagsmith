import Constants from 'common/constants'
export default (envId, { FEATURE_NAME, FEATURE_NAME_ALT }) => `<?php

use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}'${
  Constants.isCustomFlagsmithUrl()
    ? `, '${Constants.getFlagsmithSDKUrl()}'`
    : ''
});

// The method below triggers a network request
$flags = $flagsmith->getEnvironmentFlags();

// Check whether the feature is enabled, or read its value
$isEnabled = $flags->isFeatureEnabled('${FEATURE_NAME}');
$featureValue = $flags->getFeatureValue('${FEATURE_NAME_ALT || FEATURE_NAME}');
`
