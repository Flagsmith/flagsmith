module.exports = (envId, { LIB_NAME, FEATURE_NAME, TRAIT_NAME, USER_ID, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT, NPM_NODE_CLIENT }, userId) => `import ${LIB_NAME} from "${NPM_NODE_CLIENT}"; // Add this line if you're using ${LIB_NAME} via npm

await ${LIB_NAME}.setTrait("${USER_ID}", ${TRAIT_NAME}, 21)
const trait = await ${LIB_NAME}.getTrait("${USER_ID}", ${TRAIT_NAME})

`;
