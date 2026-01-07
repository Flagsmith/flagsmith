import { useState, useEffect, useCallback, useRef } from 'react'

export function useOptimisticToggle(actualValue: boolean | undefined) {
  const [optimisticValue, setOptimisticValue] = useState<boolean | null>(null)
  const [isToggling, setIsToggling] = useState(false)
  const isTogglingRef = useRef(false)

  useEffect(() => {
    setOptimisticValue(null)
    setIsToggling(false)
    isTogglingRef.current = false
  }, [actualValue])

  const displayValue = optimisticValue ?? actualValue

  const setOptimistic = useCallback((value: boolean) => {
    if (isTogglingRef.current) return false
    isTogglingRef.current = true
    setIsToggling(true)
    setOptimisticValue(value)
    return true
  }, [])

  const revertOptimistic = useCallback(() => {
    setOptimisticValue(null)
    setIsToggling(false)
    isTogglingRef.current = false
  }, [])

  return { displayValue, isToggling, revertOptimistic, setOptimistic }
}
