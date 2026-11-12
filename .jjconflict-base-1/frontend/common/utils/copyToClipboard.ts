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
    await navigator.clipboard.writeText(value)
    toast(successMessage ?? 'Copied to clipboard')
  } catch (error) {
    toast(errorMessage ?? 'Failed to copy to clipboard')
    throw error
  }
}

export default copyToClipboard
