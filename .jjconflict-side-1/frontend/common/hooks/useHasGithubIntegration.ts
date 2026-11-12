import AccountStore from 'common/stores/account-store'
import { useGetGithubIntegrationQuery } from 'common/services/useGithubIntegration'

export function useHasGithubIntegration() {
  const organisationId = AccountStore.getOrganisation()?.id
  const { data } = useGetGithubIntegrationQuery(
    { organisation_id: organisationId },
    { skip: !organisationId },
  )

  return {
    githubId: data?.results?.[0]?.id ?? '',
    hasIntegration: !!data?.results?.length,
    organisationId,
  }
}
