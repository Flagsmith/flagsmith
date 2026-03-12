import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ProjectFlag } from 'common/types/responses'

type UseEvaluationCountsOptions = {
  staleNoCodeFlags: ProjectFlag[]
  selectedEnvironments: string[]
  period: number
}

export function useEvaluationCounts({
  period,
  selectedEnvironments,
  staleNoCodeFlags,
}: UseEvaluationCountsOptions) {
  const [checkedPairs, setCheckedPairs] = useState<Set<string>>(new Set())
  const [activeFlagIds, setActiveFlagIds] = useState<Set<number>>(new Set())

  // Reset when inputs change
  useEffect(() => {
    setCheckedPairs(new Set())
    setActiveFlagIds(new Set())
  }, [staleNoCodeFlags, selectedEnvironments, period])

  const handleEvaluationResult = useCallback(
    (featureId: number, envId: string, hasEvaluations: boolean) => {
      const key = `${featureId}:${envId}`
      setCheckedPairs((prev) => {
        if (prev.has(key)) return prev
        const next = new Set(prev)
        next.add(key)
        return next
      })
      if (hasEvaluations) {
        setActiveFlagIds((prev) => {
          if (prev.has(featureId)) return prev
          const next = new Set(prev)
          next.add(featureId)
          return next
        })
      }
    },
    [],
  )

  const isCheckingEvaluations = useMemo(() => {
    if (staleNoCodeFlags.length === 0) return false
    return !staleNoCodeFlags.every((f) =>
      selectedEnvironments.every((envId) =>
        checkedPairs.has(`${f.id}:${envId}`),
      ),
    )
  }, [staleNoCodeFlags, selectedEnvironments, checkedPairs])

  const monitorFlags = useMemo(
    () => staleNoCodeFlags.filter((f) => activeFlagIds.has(f.id)),
    [staleNoCodeFlags, activeFlagIds],
  )

  const removeFlags = useMemo(
    () => staleNoCodeFlags.filter((f) => !activeFlagIds.has(f.id)),
    [staleNoCodeFlags, activeFlagIds],
  )

  return {
    handleEvaluationResult,
    isCheckingEvaluations,
    monitorCount: isCheckingEvaluations ? undefined : monitorFlags.length,
    monitorFlags,
    removeCount: isCheckingEvaluations ? undefined : removeFlags.length,
    removeFlags,
  }
}
