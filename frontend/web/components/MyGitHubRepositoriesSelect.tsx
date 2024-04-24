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
  const { data } = useGetGithubReposQuery({
    installation_id: installationId,
    organisation_id: organisationId,
  })
  return (
    <GitHubRepositoriesSelect
      githubId={githubId}
      organisationId={organisationId}
      projectId={projectId}
      repositories={data?.repositories}
    />
  )
}

export default MyGitHubRepositoriesSelect
