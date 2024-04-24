import { FC } from 'react'
import { useGetGithubRepositoriesQuery } from 'common/services/useGithubRepository'
import RepositoriesSelect from './RepositoriesSelect'

type MyRepositoriesSelectType = {
  githubId: string
  orgId: string
  onChange: () => void
}

const MyRepositoriesSelect: FC<MyRepositoriesSelectType> = ({
  githubId,
  onChange,
  orgId,
}) => {
  const { data } = useGetGithubRepositoriesQuery({
    github_id: githubId,
    organisation_id: orgId,
  })
  return <RepositoriesSelect repositories={data?.results} onChange={onChange} />
}

export default MyRepositoriesSelect
