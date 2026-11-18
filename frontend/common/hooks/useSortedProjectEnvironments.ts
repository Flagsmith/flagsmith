import { skipToken } from '@reduxjs/toolkit/query'
import { useGetAllEnvironmentsQuery } from 'common/services/useEnvironment'
import { sortEnvironmentsByName } from 'common/utils/sortEnvironmentsByName'

export const useSortedProjectEnvironments = (projectId: number | undefined) => {
  // currentData: data would keep the previous project's list while the next loads
  const { currentData, isError, isFetching, refetch } =
    useGetAllEnvironmentsQuery(projectId ? { projectId } : skipToken)
  return {
    environments: currentData && sortEnvironmentsByName(currentData),
    isError,
    isLoading: isFetching && !currentData,
    refetch,
  }
}
