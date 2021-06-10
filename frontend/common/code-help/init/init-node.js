module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_NODE_CLIENT, NPM_CLIENT }, customFeature) => `import ${LIB_NAME} from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

${LIB_NAME}.init({
    environmentID: "${envId}"
});

// Check for a feature
${LIB_NAME}.hasFeature("${customFeature || FEATURE_NAME}")
    .then((featureEnabled) => {
        if (featureEnabled) {
           ${FEATURE_FUNCTION}();
        }
    });

// Or, use the value of a feature
${LIB_NAME}.getValue("${customFeature || FEATURE_NAME_ALT}")
    .then((value) => {
        // Show a value to the world
    });
`;
