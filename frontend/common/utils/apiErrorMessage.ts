// A rejection arrives as a bare list of strings (service-layer ValidationError),
// keyed by field and sometimes nested (serializer errors), or as
// {detail: "..."}. Walking the structure covers all three.
const firstMessage = (value: unknown): string | undefined => {
  if (typeof value === 'string') return value || undefined
  if (value && typeof value === 'object') {
    for (const entry of Object.values(value)) {
      const message = firstMessage(entry)
      if (message) return message
    }
  }
  return undefined
}

export const getApiErrorMessage = (
  error: unknown,
  fallback: string,
): string => {
  const data =
    error && typeof error === 'object' && 'data' in error
      ? error.data
      : undefined
  // A bare string body is an HTML error page from a proxy rather than a DRF
  // message, so it is never worth putting in front of the user.
  if (typeof data === 'string') return fallback
  return firstMessage(data) || fallback
}
