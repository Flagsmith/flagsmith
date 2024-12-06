import Constants from 'common/constants'

module.exports = (envId, { USER_ID }, userId) => `// Identify/create user

curl -i '${Constants.getFlagsmithSDKUrl()}identities/?identifier=${
  userId || USER_ID
}' \\
     -H 'x-environment-key: ${envId}'
`
