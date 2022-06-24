module.exports = (envId, { TRAIT_NAME }, userId) => `
do {
    let trait = Trait(key: "${TRAIT_NAME}", value: 42)
    try await flagsmith.setTrait(trait, forIdentity: "${userId}")
} catch {
    print(error)
}
`;
