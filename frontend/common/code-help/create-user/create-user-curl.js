module.exports = (envId, { USER_ID }, userId) => `// Identify/create user

curl 'https://edge.api.flagsmith.com/api/v1/identities/?identifier=${
  userId || USER_ID
}'
     -H 'x-environment-key: ${envId}'
`
