import {
  DependenciesMode,
  getDependenciesMode,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab/dependenciesMode'

const cases: [boolean, boolean, DependenciesMode][] = [
  [false, false, 'direct'],
  [false, true, 'direct'],
  [true, true, 'changeRequest'],
  [true, false, 'readOnly'],
]

describe('getDependenciesMode', () => {
  it.each(cases)(
    'change requests %s, versioned %s: %s',
    (requiresChangeRequests, isVersioned, expected) => {
      expect(getDependenciesMode(requiresChangeRequests, isVersioned)).toBe(
        expected,
      )
    },
  )
})
