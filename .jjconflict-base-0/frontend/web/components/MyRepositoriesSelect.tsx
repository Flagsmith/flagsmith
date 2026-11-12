import { FC, useEffect } from 'react'
import { useGetGithubRepositoriesQuery } from 'common/services/useGithubRepository'
import RepositoriesSelect from './RepositoriesSelect'

type MyRepositoriesSelectType = {
  githubId: string
  orgId: string
  value?: string
  onChange: (value: string) => void
}

const MyRepositoriesSelect: FC<MyRepositoriesSelectType> = ({
  githubId,
  onChange,
  orgId,
  value,
}) => {
  const { data } = useGetGithubRepositoriesQuery({
    github_id: githubId,
    organisation_id: orgId,
  })

  useEffect(() => {
    if (data?.results.length === 1) {
      const repo = data?.results[0]
      onChange(`${repo.repository_name}/${repo.repository_owner}`)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  return (
    <RepositoriesSelect
      value={value}
      repositories={data?.results}
      onChange={onChange}
    />
  )
}

export default MyRepositoriesSelect
