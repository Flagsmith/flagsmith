module.exports = (envId, { TRAIT_NAME }, userId) => `require "flagsmith"

$flagsmith = Flagsmith::Client.new(
    environment_key: '${envId}'
)

traits = {"${TRAIT_NAME}": 42}

// Identify a user, set their traits and retrieve the flags
identity_flags = $flagsmith.get_identity_flags("${userId}", traits)
`;
