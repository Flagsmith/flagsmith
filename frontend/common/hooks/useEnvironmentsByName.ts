import { useMemo } from 'react'
import sortBy from 'lodash/sortBy'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import type { Environment } from 'common/types/responses'

type UseEnvironmentsByNameResult = {
  environments: Environment[] | undefined
  isLoading: boolean
  isError: boolean
}

// The API orders environments by id
export function useEnvironmentsByName(
  projectId: number | undefined,
): UseEnvironmentsByNameResult {
  const { data, isError, isLoading } = useGetEnvironmentsQuery(
    projectId ? { projectId } : skipToken,
  )
  const environments = useMemo(
    () => data && sortBy(data.results, 'name'),
    [data],
  )
  return { environments, isError, isLoading }
}
