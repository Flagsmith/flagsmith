import { useState, useEffect, useCallback } from 'react'

export function useOptimisticToggle(actualValue: boolean | undefined) {
  const [optimisticValue, setOptimisticValue] = useState<boolean | null>(null)

  useEffect(() => {
    setOptimisticValue(null)
  }, [actualValue])

  const displayValue = optimisticValue ?? actualValue

  const setOptimistic = useCallback((value: boolean) => {
    setOptimisticValue(value)
  }, [])

  const revertOptimistic = useCallback(() => {
    setOptimisticValue(null)
  }, [])

  return { displayValue, revertOptimistic, setOptimistic }
}
