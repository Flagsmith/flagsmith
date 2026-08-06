import Constants from 'common/constants'
// Flag names are user-defined and need not be valid JS identifiers, so the
// snippet reads flags by key and keeps its own local variable names.
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `import ${LIB_NAME} from "${NPM_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

${LIB_NAME}.init({
    environmentID: "${envId}",${
  Constants.isCustomFlagsmithUrl()
    ? `\n    api: "${Constants.getFlagsmithSDKUrl()}",`
    : ''
}
    onChange: (oldFlags, params) => { // Occurs whenever flags are changed
        // Determines if the update came from the server or local cached storage
        const { isFromServer } = params;

        // Check whether the feature is enabled, or read its value
        const isEnabled = ${LIB_NAME}.hasFeature("${FEATURE_NAME}");
        const featureValue = ${LIB_NAME}.getValue("${
  FEATURE_NAME_ALT || FEATURE_NAME
}");
        console.log("${FEATURE_NAME} enabled:", isEnabled, { isFromServer });
        console.log("${FEATURE_NAME_ALT || FEATURE_NAME} value:", featureValue);

        // Check whether the value has changed
        const previousValue = oldFlags["${FEATURE_NAME_ALT || FEATURE_NAME}"]
            && oldFlags["${FEATURE_NAME_ALT || FEATURE_NAME}"].value;

        if (featureValue !== previousValue) {
            // Value has changed, do something here
        }
    }
});
`
