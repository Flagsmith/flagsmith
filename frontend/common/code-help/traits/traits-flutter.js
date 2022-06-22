module.exports = (envId, { USER_ID, TRAIT_NAME }, userId) => `
final user = Identity(identifier: '${userId || USER_ID}');

// Create a new user trait for the above identity
flagsmithClient.createTrait(
    value: TraitWithIdentity(
    identity: user
    key: '${TRAIT_NAME}',
    value: '21',
    ),
);

// Update the previously created trait with a new value
flagsmithClient.updateTraits(value: [
    TraitWithIdentity(
    identity: user,
    key: '${TRAIT_NAME}',
    value: '20',
    ),
]);
`;
