import { useCallback, useEffect, useMemo, useState } from 'react'
import { fromScopedTotals } from './utils'
import { UsageScope } from './UsageScopeTotal'

/**
 * Collects the totals reported by one UsageScopeTotal per scope.
 *
 * Keyed on the scope's key rather than its label, because two projects may
 * share a name and would otherwise overwrite each other.
 *
 * `identity` is anything that changes what the totals mean: the period, the
 * project filter, the dimension. When it changes the collected totals are
 * dropped, otherwise the previous period's numbers stay on screen while the new
 * requests are still in flight, with nothing to say they are stale.
 */
export const useScopedBreakdown = (scopes: UsageScope[], identity: string) => {
  const [totals, setTotals] = useState<Record<string, number>>({})

  useEffect(() => {
    setTotals({})
  }, [identity])

  const onTotal = useCallback((key: string, total: number | undefined) => {
    if (total === undefined) {
      return
    }
    setTotals((current) =>
      current[key] === total ? current : { ...current, [key]: total },
    )
  }, [])

  const rows = useMemo(() => fromScopedTotals(scopes, totals), [scopes, totals])

  const answered = scopes.filter(
    (scope) => totals[scope.key] !== undefined,
  ).length

  return {
    isLoading: !!scopes.length && answered < scopes.length,
    onTotal,
    rows,
  }
}
