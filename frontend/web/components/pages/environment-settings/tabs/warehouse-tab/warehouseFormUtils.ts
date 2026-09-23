export const getButtonLabel = (isEdit: boolean, isSaving: boolean): string => {
  if (isSaving) return isEdit ? 'Saving...' : 'Creating...'
  return isEdit ? 'Save changes' : 'Save and continue'
}

export const getWarehouseErrorMessage = (isEdit: boolean): string =>
  `Failed to ${
    isEdit ? 'update' : 'create'
  } warehouse connection. Please try again.`

export const isMissingEventsTableDetail = (detail: string | null): boolean =>
  !!detail?.startsWith('Events table not found')

const punctuate = (detail: string): string =>
  `${detail}${/[.!?]$/.test(detail) ? '' : '.'}`

export const getTestFailureWarning = (detail: string | null): string => {
  // The missing-table detail means the connection itself succeeded, so the
  // "couldn't establish a connection" lead-in would be wrong.
  if (detail && isMissingEventsTableDetail(detail)) {
    return `${punctuate(
      detail,
    )}\nYou can save anyway and test again later, but events won't be delivered until the table exists.`
  }
  const reason = detail ? `: ${punctuate(detail)}` : '.'
  return `We couldn't establish a connection${reason}\nYou can save anyway and test again later, but events won't be delivered until the connection succeeds.`
}
