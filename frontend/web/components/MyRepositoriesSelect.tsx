import { FC } from 'react'
import { useGetGithubRepositoriesQuery } from 'common/services/useGithubRepository'
import RepositoriesSelect from './RepositoriesSelect'

type MyRepositoriesSelectType = {
  githubId: string
  organisationId: number
  onChange: () => void
}

const MyRepositoriesSelect: FC<MyRepositoriesSelectType> = ({
  githubId,
  onChange,
  organisationId,
}) => {
  const { data } = useGetGithubRepositoriesQuery({
    github_id: githubId,
    organisation_id: organisationId,
  })
  return <RepositoriesSelect repositories={data?.results} onChange={onChange} />
}

export default MyRepositoriesSelect
