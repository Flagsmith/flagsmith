module.exports = (envId, { FEATURE_NAME, TRAIT_NAME, USER_ID }) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

traits = {${TRAIT_NAME}: 42}

identity_flags = $flagsmith.get_identity_flags("${USER_ID}", traits)
@enabled = identity_flags.is_feature_enabled('${FEATURE_NAME}')
@value = identity_flags.get_feature_value('${FEATURE_NAME}')
`;
