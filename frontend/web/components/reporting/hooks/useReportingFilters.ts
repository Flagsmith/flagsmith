import { useState, useCallback } from 'react'
import moment from 'moment'

export type DateRange = {
  startDate: moment.Moment | null
  endDate: moment.Moment | null
}

export interface ReportingFilters {
  timeRange: DateRange
  projectId?: string
  environmentId?: string
}

export const useReportingFilters = (context: 'project' | 'organisation', contextId: string) => {
  const [filters, setFilters] = useState<ReportingFilters>({
    timeRange: {
      startDate: moment().subtract(30, 'days'),
      endDate: moment()
    },
    projectId: context === 'project' ? contextId : undefined,
    environmentId: undefined
  })

  const updateFilters = useCallback((newFilters: Partial<ReportingFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters({
      timeRange: {
        startDate: moment().subtract(30, 'days'),
        endDate: moment()
      },
      projectId: context === 'project' ? contextId : undefined,
      environmentId: undefined
    })
  }, [context, contextId])

  return {
    filters,
    setFilters: updateFilters,
    resetFilters
  }
}
