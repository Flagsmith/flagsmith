import { useCallback, useEffect, useMemo, useState } from 'react'
import { fromScopedTotals } from './utils'
import { UsageScope } from './components/ScopeTotal'

/**
 * Collects the totals reported by one ScopeTotal per scope, keyed on the scope
 * rather than its label because two projects may share a name.
 *
 * `identity` is anything that changes what the totals mean: period, project,
 * dimension. Without dropping them on a change, the previous period's numbers
 * stay on screen while the new requests are in flight, marked as current.
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
