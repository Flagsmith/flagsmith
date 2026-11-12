import { useCallback, useEffect, useRef } from 'react'

export default function useDebounce(func: any, delay: number) {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const funcRef = useRef(func)

  // Keep the latest callback without re-creating the debounced function,
  // so the caller doesn't have to memoise `func` themselves.
  useEffect(() => {
    funcRef.current = func
  }, [func])

  useEffect(
    () => () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    },
    [],
  )

  return useCallback(
    (...args: any[]) => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        funcRef.current(...args)
      }, delay)
    },
    [delay],
  ) as typeof func
}
/* Usage example:
const searchItems = useDebounce((search:string) => {
  doThing()
}, 500)
*/
