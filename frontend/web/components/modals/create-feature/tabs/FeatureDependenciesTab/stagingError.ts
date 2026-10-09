export type StagingError = { message: string; prerequisiteId?: number }

const isStagingError = (e: unknown): e is StagingError =>
  typeof e === 'object' &&
  e !== null &&
  typeof (e as StagingError).message === 'string'

// The API answers with { message }, { detail } or { field: [messages] }.
export const describeApiError = (e: unknown): string | undefined => {
  const data = typeof e === 'object' && e !== null && 'data' in e && e.data
  if (!data || typeof data !== 'object') return
  if ('message' in data && typeof data.message === 'string') return data.message
  if ('detail' in data && typeof data.detail === 'string') return data.detail
  const [field, messages] = Object.entries(data)[0] ?? []
  return field
    ? `${field}: ${([] as unknown[]).concat(messages).join(' ')}`
    : undefined
}

export const toStagingError = (e: unknown, fallback: string): StagingError =>
  isStagingError(e) ? e : { message: describeApiError(e) ?? fallback }
