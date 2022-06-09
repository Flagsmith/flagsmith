import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}');

// Check for a feature
$${FEATURE_NAME} = $flags->isFeatureEnabled('${FEATURE_NAME}');

// Or use the value of a feature
$${FEATURE_NAME_ALT} = $flags->getFeatureValue('${FEATURE_NAME_ALT}')
`;
