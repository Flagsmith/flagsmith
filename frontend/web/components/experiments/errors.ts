// Audience and rollout rejections are raised as DRF ValidationErrors from the
// service layer, so the body arrives as a bare list of strings. Serializer-level
// failures arrive keyed by field instead — nested one level under
// `experiment_rollout` for the rollout body — and auth or routing failures as
// {detail: "..."}. Walking the structure covers all of them.
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
