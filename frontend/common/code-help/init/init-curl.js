module.exports = (envId) => `
curl -i '${Project.flagsmithClientAPI}flags/' \\
     -H 'x-environment-key: ${envId}'
`
