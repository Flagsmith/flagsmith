export const getButtonLabel = (isEdit: boolean, isSaving: boolean): string => {
  if (isSaving) return isEdit ? 'Saving...' : 'Creating...'
  return isEdit ? 'Save changes' : 'Save and continue'
}
