import Constants from 'common/constants'

module.exports = (envId, { USER_ID }, userId) => {
  const url = new URL('identities/', Constants.getFlagsmithSDKUrl())
  url.searchParams.append('identifier', userId || USER_ID)

  return `// Identify/create user

curl -i '${url}' \\
     -H 'X-Environment-Key: ${envId}'`
}
