import { getDependenciesMode } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/dependenciesMode'

describe('getDependenciesMode', () => {
  it.each([
    [false, false, 'direct'],
    [false, true, 'direct'],
    [true, true, 'changeRequest'],
    [true, false, 'readOnly'],
  ] as const)(
    'change requests %s, versioned %s: %s',
    (requiresChangeRequests, isVersioned, expected) => {
      expect(getDependenciesMode(requiresChangeRequests, isVersioned)).toBe(
        expected,
      )
    },
  )
})
