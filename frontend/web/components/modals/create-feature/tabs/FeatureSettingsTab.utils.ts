type GetRemoveFeatureDisabledReasonParams = {
  isProtected: boolean
  isRemoving: boolean
  isSaving: boolean
}

export const getRemoveFeatureDisabledReason = ({
  isProtected,
  isRemoving,
  isSaving,
}: GetRemoveFeatureDisabledReasonParams): string | null => {
  if (isProtected) {
    return 'This feature has a permanent tag. Remove it before deleting the feature.'
  }

  if (isRemoving) {
    return 'The feature is being removed.'
  }

  if (isSaving) {
    return 'Wait for the current feature update to finish.'
  }

  return null
}
