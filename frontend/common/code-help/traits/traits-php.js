import Constants from 'common/constants'
module.exports = (envId, { TRAIT_NAME }, userId) => `use Flagsmith\\Flagsmith;

$flagsmith = new Flagsmith('${envId}'${
  Constants.isCustomFlagsmithUrl && `,\n  '${Constants.getFlagsmithSDKUrl()}'\n`
});

$traits = (object) [ '${TRAIT_NAME}' => 42 ];

// Identify a user, set their traits and retrieve the flags
$flags = $flagsmith->getIdentityFlags("${userId}", $traits);
`
