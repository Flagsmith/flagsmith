// usage-data allows five requests a minute per user, so a 429 is a wait, not
// a failure.
export const isThrottled = (error: unknown): boolean =>
  typeof error === 'object' &&
  error !== null &&
  (error as { status?: unknown }).status === 429

export const THROTTLED = {
  description:
    'Usage is limited to a few requests a minute. Try again in a minute.',
  title: 'Too many requests',
}
