module.exports = (envId, { LIB_NAME, NPM_RN_CLIENT, USER_ID, USER_FEATURE_FUNCTION, USER_FEATURE_NAME }, userId) => `import ${LIB_NAME} from '${NPM_RN_CLIENT}';

${LIB_NAME}.init({
    environmentID: "${envId}",
        onChange: (oldFlags, params) => { // Occurs whenever flags are changed
        // Determines if the update came from the server or local cached storage
        const { isFromServer } = params;

        // Check for a feature
        if (${LIB_NAME}.hasFeature("${USER_FEATURE_NAME}")) {
            ${USER_FEATURE_FUNCTION}();
        }

        // Or, use the value of a feature
        const ${USER_FEATURE_NAME} = ${LIB_NAME}.getValue("${USER_FEATURE_NAME}");

        // Check whether value has changed
        const ${USER_FEATURE_NAME}Old = oldFlags["${USER_FEATURE_NAME}"] 
        && oldFlags["${USER_FEATURE_NAME}"].value;
        if (${USER_FEATURE_NAME} !== ${USER_FEATURE_NAME}Old) {
            // Value has changed, do something here
        }
    }
});

// This will create a user in the dashboard if they don't already exist.
${LIB_NAME}.identify("${userId || USER_ID}"); 

`;
