module.exports = (envId, { SEGMENT_NAME, FEATURE_FUNCTION, LIB_NAME, NPM_CLIENT, TRAIT_NAME, USER_ID, USER_FEATURE_FUNCTION, USER_FEATURE_NAME }, userId) => `${LIB_NAME}.identify("${userId || USER_ID}"); // This will create a user in the dashboard if they don't already exist

// Set a user trait, setting traits will retrieve new flags and trigger an onChange event
${LIB_NAME}.setTrait("${TRAIT_NAME}", 21);
`;
