module.exports = (
  envId,
  { TRAIT_NAME, USER_ID },
  userId,
) => `curl -i -X POST '${Project.flagsmithClientAPI}identities/' \\
     -H 'x-environment-key: ${envId}' \\
     -H 'Content-Type: application/json; charset=utf-8' \\
     -d $'{
  "traits": [
    {
      "trait_key": "${TRAIT_NAME}",
      "trait_value": 42
    }
  ],
  "identifier": "${userId || USER_ID}"
}'
`
