import { useMemo, useState } from 'react'
import { Res } from 'common/types/responses'
import { byRequestType, bySdk, BreakdownDimension } from './utils'

type UseUsageBreakdown = {
  data: Res['organisationUsage'] | undefined
}

export const useUsageBreakdown = ({ data }: UseUsageBreakdown) => {
  const [dimension, setDimension] = useState<BreakdownDimension>('request-type')

  const rows = useMemo(
    () => (dimension === 'sdk' ? bySdk(data) : byRequestType(data)),
    [dimension, data],
  )

  return { dimension, rows, setDimension }
}
