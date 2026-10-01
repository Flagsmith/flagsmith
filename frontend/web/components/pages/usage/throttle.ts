import { useEffect, useRef, useState } from 'react'

// usage-data is throttled at five requests a minute per user. The API sends
// Retry-After, but it is not exposed to the browser across origins.
export const THROTTLE_WINDOW_SECONDS = 60

export const isThrottled = (error: unknown): boolean =>
  typeof error === 'object' &&
  error !== null &&
  (error as { status?: unknown }).status === 429

/** Counts down once throttled, then retries. Undefined while not throttled. */
export const useThrottleRetry = (
  throttled: boolean,
  retry: () => void,
): number | undefined => {
  const [secondsLeft, setSecondsLeft] = useState<number>()
  const retryRef = useRef(retry)
  retryRef.current = retry

  useEffect(() => {
    if (!throttled) {
      setSecondsLeft(undefined)
      return
    }
    const startedAt = Date.now()
    setSecondsLeft(THROTTLE_WINDOW_SECONDS)
    const timer = setInterval(() => {
      const left =
        THROTTLE_WINDOW_SECONDS - Math.floor((Date.now() - startedAt) / 1000)
      if (left <= 0) {
        clearInterval(timer)
        retryRef.current()
        return
      }
      setSecondsLeft(left)
    }, 1000)
    return () => clearInterval(timer)
  }, [throttled])

  return secondsLeft
}

export const throttledMessage = (secondsLeft: number): string =>
  `Usage is limited to a few requests a minute. Retrying in ${secondsLeft}s.`
