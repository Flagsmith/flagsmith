export const getButtonLabel = (isEdit: boolean, isSaving: boolean): string => {
  if (isSaving) return isEdit ? 'Saving...' : 'Creating...'
  return isEdit ? 'Save changes' : 'Save and continue'
}

export const getWarehouseErrorMessage = (isEdit: boolean): string =>
  `Failed to ${
    isEdit ? 'update' : 'create'
  } warehouse connection. Please try again.`

export const getTestFailureWarning = (detail: string | null): string => {
  const reason = detail ? `: ${detail}${/[.!?]$/.test(detail) ? '' : '.'}` : '.'
  return `We couldn't establish a connection${reason} You can save anyway and test again later, but events won't be delivered until the connection succeeds.`
}
