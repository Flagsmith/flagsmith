// The fields the forms render errors against inline.
const FIELD_NAMES = ['audience', 'issuer', 'name'] as const

export type TrustRelationshipFieldName = (typeof FIELD_NAMES)[number]
export type TrustRelationshipFieldErrors = Partial<
  Record<TrustRelationshipFieldName, string>
>

const isFieldName = (key: string): key is TrustRelationshipFieldName =>
  FIELD_NAMES.includes(key as TrustRelationshipFieldName)

// A DRF error body arrives as {detail: "..."}, {field: ["..."]}, or
// {non_field_errors: ["..."]}. Anything else — an HTML error page served by a
// proxy, say — is not ours to render, so it never leaves this module.
const errorBody = (error: unknown): Record<string, unknown> | undefined => {
  const data = (error as { data?: unknown } | undefined)?.data
  return data && typeof data === 'object' && !Array.isArray(data)
    ? (data as Record<string, unknown>)
    : undefined
}

const firstMessage = (value: unknown): string | undefined => {
  if (typeof value === 'string') {
    return value
  }
  if (Array.isArray(value) && typeof value[0] === 'string') {
    return value[0]
  }
  return undefined
}

// Extracts the first human-readable message from an error body.
export const trustRelationshipErrorMessage = (
  error: unknown,
  fallback: string,
): string => {
  const body = errorBody(error)
  const first = body && firstMessage(Object.values(body)[0])
  return first || fallback
}

// The messages that belong on their own input.
export const trustRelationshipFieldErrors = (
  error: unknown,
): TrustRelationshipFieldErrors => {
  const body = errorBody(error)
  if (!body) {
    return {}
  }
  return FIELD_NAMES.reduce<TrustRelationshipFieldErrors>((errors, name) => {
    const message = firstMessage(body[name])
    return message ? { ...errors, [name]: message } : errors
  }, {})
}

// The alert carries whatever has no field to attach to. Null means every
// message is already rendered inline.
export const trustRelationshipAlertError = (
  error: unknown,
  fallback: string,
): string | null => {
  if (!error) {
    return null
  }
  const body = errorBody(error)
  if (!body || !Object.keys(body).length) {
    return fallback
  }
  const rest = Object.entries(body).filter(([key]) => !isFieldName(key))
  if (!rest.length) {
    return null
  }
  const messages = rest
    .map(([, value]) => firstMessage(value))
    .filter((message): message is string => !!message)
  return messages.length ? messages.join(' ') : fallback
}
