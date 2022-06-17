module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

trait_key = params.get(:flagsmith, :trait_key)
trait_value = params.get(:flagsmith, :trait_value)
traits = trait_key.nil? ? nil : { trait_key: trait_value }

identity_flags = $flagsmith.get_identity_flags("delboy@trotterstraders.co.uk", traits)
@show_button = identity_flags.is_feature_enabled('secret_button')
@button_color = JSON.parse(identity_flags.get_feature_value('secret_button'))['colour']
`;
