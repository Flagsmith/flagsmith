module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `# This will create a user in the dashboard if they don't already exist
curl 'https://api.flagsmith.com/api/v1/identities/?identifier=${USER_ID}' \\
  -H 'x-environment-key: ${envId}' \\
  --compressed`;
