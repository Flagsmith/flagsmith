import { useMemo, useState } from 'react'
import { Res } from 'common/types/responses'
import { byRequestType, bySdk, BreakdownDimension, BreakdownRow } from './utils'

type UseUsageBreakdown = {
  data: Res['organisationUsage'] | undefined
}

export const useUsageBreakdown = ({ data }: UseUsageBreakdown) => {
  const [dimension, setDimension] = useState<BreakdownDimension>('request-type')

  const rows = useMemo((): BreakdownRow[] | undefined => {
    if (dimension === 'request-type') return byRequestType(data)
    if (dimension === 'sdk') return bySdk(data)
    return undefined
  }, [dimension, data])

  return { dimension, rows, setDimension }
}
