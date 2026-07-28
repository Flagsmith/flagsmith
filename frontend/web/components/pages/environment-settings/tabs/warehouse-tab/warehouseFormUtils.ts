export const getButtonLabel = (isEdit: boolean, isSaving: boolean): string => {
  if (isSaving) return isEdit ? 'Saving...' : 'Creating...'
  return isEdit ? 'Save changes' : 'Save and continue'
}

export const getWarehouseErrorMessage = (isEdit: boolean): string =>
  `Failed to ${
    isEdit ? 'update' : 'create'
  } warehouse connection. Please try again.`

export const getTestFailureWarning = (detail: string | null): string => {
  // The missing-table detail means the connection itself succeeded, so the
  // "couldn't establish a connection" lead-in would be wrong.
  if (detail?.startsWith('Events table not found')) {
    return `${detail} You can save anyway and test again later, but events won't be delivered until the table exists.`
  }
  const reason = detail ? `: ${detail}${/[.!?]$/.test(detail) ? '' : '.'}` : '.'
  return `We couldn't establish a connection${reason} You can save anyway and test again later, but events won't be delivered until the connection succeeds.`
}
