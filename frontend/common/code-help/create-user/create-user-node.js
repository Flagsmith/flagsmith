module.exports = (envId, { LIB_NAME, FEATURE_NAME, USER_ID, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, userId) => `import ${LIB_NAME} from "${NPM_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

${LIB_NAME}.init({
    environmentID:"${envId}"
});

// This will create a user in the dashboard if they don't already exist
${LIB_NAME}.hasFeature("${FEATURE_NAME}", "${userId || USER_ID}")
    .then((featureEnabled) => {
        if (featureEnabled) {
            // Show my awesome cool new feature to the world
        }
    });

${LIB_NAME}.getValue("${FEATURE_NAME_ALT}", "${userId || USER_ID}")
    .then((value) => {
        // Show a value to the world
    });
`;
