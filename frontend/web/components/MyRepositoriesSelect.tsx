import { FC } from 'react'
import { useGetGithubRepositoriesQuery } from 'common/services/useGithubRepository'
import RepositoriesSelect from './RepositoriesSelect'

type MyRepositoriesSelectType = {
  githubId: string
  orgId: string
}

const MyRepositoriesSelect: FC<MyRepositoriesSelectType> = ({
  githubId,
  orgId,
}) => {
  const { data } = useGetGithubRepositoriesQuery({
    github_id: githubId,
    organisation_id: orgId,
  })
  return <RepositoriesSelect repositories={data?.results} />
}

export default MyRepositoriesSelect
