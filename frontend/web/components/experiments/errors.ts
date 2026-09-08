// A rejection arrives as a bare list of strings (service-layer ValidationError),
// keyed by field and sometimes nested under `experiment_rollout` (serializer),
// or as {detail: "..."}. Walking the structure covers all three.
const firstMessage = (value: unknown): string | undefined => {
  if (typeof value === 'string') return value || undefined
  if (Array.isArray(value) || (value && typeof value === 'object')) {
    for (const entry of Object.values(value as object)) {
      const message = firstMessage(entry)
      if (message) return message
    }
  }
  return undefined
}

type ErrorWithData = { data?: unknown } | undefined

export const experimentErrorMessage = (
  error: unknown,
  fallback: string,
): string => {
  const data = (error as ErrorWithData)?.data
  // A bare string body is an HTML error page from a proxy rather than a DRF
  // message, so it is never worth putting in front of the user.
  if (typeof data === 'string') return fallback
  return firstMessage(data) || fallback
}
