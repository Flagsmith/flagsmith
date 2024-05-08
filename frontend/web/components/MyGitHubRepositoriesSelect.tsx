import { FC } from 'react'
import { useGetGithubReposQuery } from 'common/services/useGithub'
import GitHubRepositoriesSelect from './GitHubRepositoriesSelect'

type MyGitHubRepositoriesSelectType = {
  installationId: string
  organisationId: string
  projectId: string
  githubId: string
}

const MyGitHubRepositoriesSelect: FC<MyGitHubRepositoriesSelectType> = ({
  githubId,
  installationId,
  organisationId,
  projectId,
}) => {
  const { data, isFetching } = useGetGithubReposQuery({
    installation_id: installationId,
    organisation_id: organisationId,
  })

  console.log('DEBUG: data:', data)

  return (
    <>
      {isFetching ? (
        <div className='text-center'>
          <Loader />
        </div>
      ) : (
        <GitHubRepositoriesSelect
          githubId={githubId}
          organisationId={organisationId}
          projectId={projectId}
          repositories={data?.repositories}
        />
      )}
    </>
  )
}

export default MyGitHubRepositoriesSelect
