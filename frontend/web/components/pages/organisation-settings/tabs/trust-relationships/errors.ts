// Extracts the first human-readable message from a DRF error body, which
// arrives as {detail: "..."}, {field: ["..."]}, or {non_field_errors: ["..."]}.
export const trustRelationshipErrorMessage = (
  error: unknown,
  fallback: string,
): string => {
  const data = (error as { data?: unknown })?.data
  if (data && typeof data === 'object') {
    const first = Object.values(data as Record<string, unknown>)[0]
    if (typeof first === 'string') {
      return first
    }
    if (Array.isArray(first) && typeof first[0] === 'string') {
      return first[0]
    }
  }
  return fallback
}
