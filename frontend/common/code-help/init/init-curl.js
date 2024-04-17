module.exports = (envId) => `
curl -i 'https://edge.api.flagsmith.com/api/v1/flags/' \\
     -H 'x-environment-key: ${envId}'
`
