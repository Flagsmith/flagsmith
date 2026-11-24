import {
  getApiErrorMessage,
  getApiErrorMessages,
} from 'common/utils/apiErrorMessage'

const FALLBACK = 'Could not save this feature. Please try again.'
const NO_CHANGES_WARNING =
  'Your feature contains no changes to its value, enabled state or environment weights. If you have adjusted any variation values this will have been saved for all environments.'

export type SaveFeedback = {
  error: string
  warning: string
}

// A save fails with a thrown Error (raw or serialised by RTK), an API response
// ({ status, data }) or a bare API body from the older save path.
const getErrorText = (error: unknown): string => {
  if (!error) return ''
  if (typeof error === 'string') return error
  // An Error, or one RTK serialised to { name, message, stack }.
  if (
    typeof error === 'object' &&
    'message' in error &&
    typeof error.message === 'string'
  ) {
    return error.message
  }
  if (typeof error === 'object' && 'data' in error) {
    return getApiErrorMessage(error, FALLBACK)
  }
  return getApiErrorMessages(error).join(' ') || FALLBACK
}

export const getSaveFeedback = (
  error: unknown,
  hasVariations: boolean,
): SaveFeedback => {
  const text = getErrorText(error)
  if (hasVariations && text.includes('no changes')) {
    return { error: '', warning: NO_CHANGES_WARNING }
  }
  return { error: text, warning: '' }
}
