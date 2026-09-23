import { useCallback, useEffect, useState } from 'react'

export const formatCountdown = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

// Counts down a number of seconds to zero, one tick per second.
// Returns the remaining value (null once finished) and a setter to (re)start it.
export const useCountdown = (): [number | null, (seconds: number) => void] => {
  const [remaining, setRemaining] = useState<number | null>(null)

  useEffect(() => {
    if (remaining === null || remaining <= 0) return
    const timer = setTimeout(
      () => setRemaining((prev) => (prev && prev > 1 ? prev - 1 : null)),
      1000,
    )
    return () => clearTimeout(timer)
  }, [remaining])

  const start = useCallback(
    (seconds: number) => setRemaining(seconds > 0 ? seconds : null),
    [],
  )

  return [remaining, start]
}

export default useCountdown
