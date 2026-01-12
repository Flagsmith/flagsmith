import { useState, useEffect, useCallback, useRef } from 'react'

/**
 * Manages feature row state including optimistic toggle updates and loading states.
 * Consolidates all row-level state management into a single hook.
 */
export function useFeatureRowState(actualEnabled: boolean | undefined) {
  const [optimisticValue, setOptimisticValue] = useState<boolean | null>(null)
  const [isToggling, setIsToggling] = useState(false)
  const [isRemoving, setIsRemoving] = useState(false)
  const isTogglingRef = useRef(false)

  // Reset optimistic state when actual value changes (after API response)
  useEffect(() => {
    setOptimisticValue(null)
    setIsToggling(false)
    isTogglingRef.current = false
  }, [actualEnabled])

  const displayEnabled = optimisticValue ?? actualEnabled
  const isLoading = isToggling || isRemoving

  const startToggle = useCallback((value: boolean) => {
    if (isTogglingRef.current) return false
    isTogglingRef.current = true
    setIsToggling(true)
    setOptimisticValue(value)
    return true
  }, [])

  const revertToggle = useCallback(() => {
    setOptimisticValue(null)
    setIsToggling(false)
    isTogglingRef.current = false
  }, [])

  const startRemoving = useCallback(() => {
    setIsRemoving(true)
  }, [])

  const stopRemoving = useCallback(() => {
    setIsRemoving(false)
  }, [])

  return {
    displayEnabled,
    isLoading,
    isRemoving,
    isToggling,
    revertToggle,
    startRemoving,
    startToggle,
    stopRemoving,
  }
}
