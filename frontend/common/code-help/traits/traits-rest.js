module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `# This will create a user in the dashboard if they don't already exist

curl -X "POST" "https://edge.api.flagsmith.com/api/v1/identities/"
     -H 'X-Environment-Key: ${envId}'
     -H 'Content-Type: application/json; charset=utf-8'
     -d $'{
  "traits": [
    {
      "trait_value": 1000,
      "trait_key": "gagan_1"
    },
    {
      "trait_value": true,
      "trait_key": "my_other_key"
    },
    {
      "trait_value": "ben2",
      "trait_key": "my_other_key_string"
    }
  ],
  "identifier": "winning2"
}'
`;
