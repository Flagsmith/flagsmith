module.exports = (envId, { USER_ID }, userId) => `// Identify/create user

curl -i '${Project.flagsmithClientAPI}identities/?identifier=${
  userId || USER_ID
}' \\
     -H 'x-environment-key: ${envId}'
`
