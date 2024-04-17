module.exports = (
  envId,
  { LIB_NAME, TRAIT_NAME, USER_ID },
  userId,
) => `// Option 1: initialise with an identity and traits
${LIB_NAME}.init({
    environmentID: "${envId}",
    identity: "${userId || USER_ID}",
    traits: { "${TRAIT_NAME}": 21 },
    onChange: (oldFlags, params) => { /* ... */ },
});

// Option 2: identify/set traits after initialising
${LIB_NAME}.identify("${userId || USER_ID}", { "${TRAIT_NAME}": 21 });
${LIB_NAME}.setTraits({ "${TRAIT_NAME}": 21 });
`
