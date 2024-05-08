import { FC } from 'react'
import { useGetGithubReposQuery } from 'common/services/useGithub'
import GitHubRepositoriesSelect from './GitHubRepositoriesSelect'
import InvalidGithubIntegration from './modals/InvalidGithubIntegration'

type MyGitHubRepositoriesSelectType = {
  installationId: string
  organisationId: string
  projectId: string
  githubId: string
  manageIntegration: () => void
  onComplete: () => void
}

const MyGitHubRepositoriesSelect: FC<MyGitHubRepositoriesSelectType> = ({
  githubId,
  installationId,
  manageIntegration,
  onComplete,
  organisationId,
  projectId,
}) => {
  const { data, error, isError, isFetching } = useGetGithubReposQuery({
    installation_id: installationId,
    is_github_installation: 'False',
    organisation_id: organisationId,
  })
  return (
    <>
      {isFetching ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : !isError && data ? (
        <GitHubRepositoriesSelect
          githubId={githubId}
          organisationId={organisationId}
          projectId={projectId}
          repositories={data?.repositories}
          manageIntegration={manageIntegration}
        />
      ) : (
        <InvalidGithubIntegration
          organisationId={organisationId}
          githubIntegrationId={githubId}
          errorMessage={error?.data?.detail}
          onComplete={onComplete}
        />
      )}
    </>
  )
}

export default MyGitHubRepositoriesSelect
