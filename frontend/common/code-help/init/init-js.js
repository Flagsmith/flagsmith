module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `import ${LIB_NAME} from "${NPM_CLIENT}"; //Add this line if you're using ${LIB_NAME} via npm

${LIB_NAME}.init({
    environmentID:"${envId}",
    onChange: (oldFlags, params) => { // Occurs whenever flags are changed
        // Determines if the update came from the server or local cached storage
        const { isFromServer } = params; 

        // Check for a feature
        if (${LIB_NAME}.hasFeature("${customFeature || FEATURE_NAME}")) {
            ${FEATURE_FUNCTION}();
        }

        // Or, use the value of a feature
        const ${FEATURE_NAME_ALT} = ${LIB_NAME}.getValue("${customFeature || FEATURE_NAME_ALT}");

        // Check whether value has changed
        const ${FEATURE_NAME_ALT}Old = oldFlags["${customFeature || FEATURE_NAME_ALT}"] 
        && oldFlags["${customFeature || FEATURE_NAME_ALT}"].value;
        
        if (${FEATURE_NAME_ALT} !== ${FEATURE_NAME_ALT}Old) {
            // Value has changed, do something here
        }
    }
});
`;
