import { useCallback, useMemo, useState } from 'react'
import { BreakdownRow } from './utils'
import { UsageScope } from './UsageScopeTotal'

/**
 * Collects the totals reported by one UsageScopeTotal per scope, and hands
 * back rows once they arrive. Scopes that have not answered yet are simply
 * absent, so the list fills in rather than blocking on the slowest request.
 */
export const useScopedBreakdown = (scopes: UsageScope[]) => {
  const [totals, setTotals] = useState<Record<string, number>>({})

  const onTotal = useCallback((label: string, total: number | undefined) => {
    if (total === undefined) {
      return
    }
    setTotals((current) =>
      current[label] === total ? current : { ...current, [label]: total },
    )
  }, [])

  const rows: BreakdownRow[] = useMemo(
    () =>
      scopes
        .filter((scope) => !!totals[scope.label])
        .map((scope) => ({ label: scope.label, value: totals[scope.label] }))
        .sort((a, b) => b.value - a.value),
    [scopes, totals],
  )

  const answered = scopes.filter(
    (scope) => totals[scope.label] !== undefined,
  ).length

  return { isLoading: !!scopes.length && answered === 0, onTotal, rows }
}
