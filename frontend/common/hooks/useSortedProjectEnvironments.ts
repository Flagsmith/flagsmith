import { useMemo } from 'react'
import sortBy from 'lodash/sortBy'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetAllEnvironmentsQuery } from 'common/services/useEnvironment'
import type { Environment } from 'common/types/responses'

type UseSortedProjectEnvironmentsResult = {
  environments: Environment[] | undefined
  isLoading: boolean
  isError: boolean
}

// The API orders environments by id
export function useSortedProjectEnvironments(
  projectId: number | undefined,
): UseSortedProjectEnvironmentsResult {
  // currentData, not data: data keeps the previous project's list while the next one loads
  const { currentData, isError, isFetching } = useGetAllEnvironmentsQuery(
    projectId ? { projectId } : skipToken,
  )
  const environments = useMemo(
    () => currentData && sortBy(currentData, 'name'),
    [currentData],
  )
  return { environments, isError, isLoading: isFetching && !currentData }
}
