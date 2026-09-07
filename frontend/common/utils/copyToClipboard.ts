// navigator.clipboard exists only in a secure context, and self-hosted
// dashboards are often served over plain http on a private network, so keep
// the execCommand path for them.
const copyWithExecCommand = (value: string): boolean => {
  const textarea = document.createElement('textarea')
  textarea.value = value
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    return document.execCommand('copy')
  } finally {
    document.body.removeChild(textarea)
  }
}

/**
 * Write `value` to the clipboard and toast the outcome.
 *
 * Rethrows after toasting so callers that need to react to a failure can,
 * but the toast means most callers do not have to.
 */
export const copyToClipboard = async (
  value: string,
  successMessage?: string,
  errorMessage?: string,
) => {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(value)
    } else if (!copyWithExecCommand(value)) {
      throw new Error('Clipboard copy was rejected')
    }
    toast(successMessage ?? 'Copied to clipboard')
  } catch (error) {
    toast(errorMessage ?? 'Failed to copy to clipboard')
    throw error
  }
}

export default copyToClipboard
