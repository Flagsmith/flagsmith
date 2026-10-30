import { experimentErrorMessage } from 'components/experiments/errors'

// The API's own message, e.g. {"config": {"host": ["..."]}}, or null.
export const getApiErrorDetail = (error: unknown): string | null =>
  experimentErrorMessage(error, '') || null

export const invalidIf = (
  value: string,
  isValid: boolean,
  message: string,
): string | false => !!value.trim() && !isValid && message

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

export const STARTING_SAVE_ANYWAY = 'You can save anyway and test again later.'

export const isWarehouseStartingDetail = (detail: string | null): boolean =>
  !!detail?.startsWith('The SQL warehouse is starting.')

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
