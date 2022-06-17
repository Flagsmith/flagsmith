module.exports = (envId, { TRAIT_NAME }, userId) => `
// Identify a user, set their traits and retrieve the flags
curl 'https://edge.api.flagsmith.com/api/v1/identities/' -H 'authority: edge.api.flagsmith.com' -H 'x-environment-key: ${envId}' -H 'content-type: application/json; charset=UTF-8' --data-binary '{"identifier":"${userId}","traits":[{"trait_key":"${TRAIT_NAME}","trait_value":"example_value"}]}' --compressed
`;
