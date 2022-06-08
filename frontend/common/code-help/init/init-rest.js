import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `curl 'https://edge.api.flagsmith.com/api/v1/flags/' -H 'X-Environment-Key: ${envId}'
`;
