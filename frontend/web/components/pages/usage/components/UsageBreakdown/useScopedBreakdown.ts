import { useCallback, useEffect, useMemo, useState } from 'react'
import { fromScopedTotals } from './utils'
import { UsageScope } from './components/ScopeTotal'

export const useScopedBreakdown = (scopes: UsageScope[], identity: string) => {
  const [totals, setTotals] = useState<Record<string, number | null>>({})

  useEffect(() => {
    setTotals({})
  }, [identity])

  const onTotal = useCallback(
    (key: string, total: number | null | undefined) => {
      if (total === undefined) {
        return
      }
      setTotals((current) =>
        current[key] === total ? current : { ...current, [key]: total },
      )
    },
    [],
  )

  const rows = useMemo(() => fromScopedTotals(scopes, totals), [scopes, totals])

  const answered = scopes.filter((scope) => scope.key in totals).length

  return {
    isLoading: !!scopes.length && answered < scopes.length,
    onTotal,
    rows,
  }
}
