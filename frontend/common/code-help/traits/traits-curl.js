module.exports = (envId, { SEGMENT_NAME, FEATURE_FUNCTION, LIB_NAME, NPM_RN_CLIENT, TRAIT_NAME, USER_FEATURE_FUNCTION, USER_FEATURE_NAME }, USER_ID) => `
// Set trait
curl 'https://api.flagsmith.com/api/v1/traits/' -H 'authority: api.bullet-train.io' -H 'x-environment-key: ${envId}' -H 'content-type: application/json; charset=UTF-8' --data-binary '{"identity":{"identifier":"${USER_ID}"},"trait_key":"${USER_FEATURE_NAME}","trait_value":"example_value"}' --compressed
// Increment trait value
curl 'https://api.flagsmith.com/api/v1/traits/increment-value/' -H 'authority: api.bullet-train.io' -H 'x-environment-key: ${envId}' -H 'origin: null' -H 'content-type: application/json; charset=UTF-8' --data-binary '{"trait_key":"${USER_FEATURE_NAME}","increment_by":1,"identifier":"bullet_train_sample_user"}' --compressed
`;
