module.exports = (
  envId,
  {
    LIB_NAME,
    NPM_CLIENT,
    TRAIT_NAME,
    USER_FEATURE_FUNCTION,
    USER_FEATURE_NAME,
    USER_ID,
  },
  userId,
) => `import ${LIB_NAME} from '${NPM_CLIENT}';

// Option 1: initialise with an identity and traits
${LIB_NAME}.init({
    environmentID: "${envId}",
    identity: "${userId || USER_ID}",
    traits: { "${TRAIT_NAME}": 21 },
    onChange: (oldFlags, params) => { /* ... */ },
});

// Option 2: identify after initialising
${LIB_NAME}.identify("${userId || USER_ID}", { "${TRAIT_NAME}": 21 });
`
