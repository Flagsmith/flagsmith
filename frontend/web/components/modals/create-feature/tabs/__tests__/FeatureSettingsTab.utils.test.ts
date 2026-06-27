import { getRemoveFeatureDisabledReason } from 'components/modals/create-feature/tabs/FeatureSettingsTab.utils'

describe('getRemoveFeatureDisabledReason', () => {
  it('disables removal when the feature has permanent tags', () => {
    expect(
      getRemoveFeatureDisabledReason({
        isProtected: true,
        isRemoving: false,
        isSaving: false,
      }),
    ).toBe(
      'This feature has a permanent tag. Remove it before deleting the feature.',
    )
  })

  it('disables removal while the feature is saving or being removed', () => {
    expect(
      getRemoveFeatureDisabledReason({
        isProtected: false,
        isRemoving: false,
        isSaving: true,
      }),
    ).toBe('Wait for the current feature update to finish.')

    expect(
      getRemoveFeatureDisabledReason({
        isProtected: false,
        isRemoving: true,
        isSaving: false,
      }),
    ).toBe('The feature is being removed.')
  })

  it('allows removal when no blocking condition applies', () => {
    expect(
      getRemoveFeatureDisabledReason({
        isProtected: false,
        isRemoving: false,
        isSaving: false,
      }),
    ).toBeNull()
  })
})
