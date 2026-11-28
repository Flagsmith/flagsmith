import { skipToken } from '@reduxjs/toolkit/query'
import { useCurrentOrganisation } from './useCurrentOrganisation'
import { useGetGithubIntegrationQuery } from 'common/services/useGithubIntegration'

export function useHasGithubIntegration() {
  const organisationId = useCurrentOrganisation()?.id
  const { currentData: data } = useGetGithubIntegrationQuery(
    organisationId ? { organisation_id: organisationId } : skipToken,
  )

  return {
    githubId: data?.results?.[0]?.id ?? '',
    hasIntegration: !!data?.results?.length,
    organisationId,
  }
}
