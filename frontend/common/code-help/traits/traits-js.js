module.exports = (
  envId,
  { LIB_NAME, TRAIT_NAME, USER_ID },
  userId,
) => `${LIB_NAME}.identify("${
  userId || USER_ID
}"); // This will create a user in the dashboard if they don't already exist

// Set a user trait, setting traits will retrieve new flags and trigger an onChange event
${LIB_NAME}.setTrait("${TRAIT_NAME}", 21);
`
