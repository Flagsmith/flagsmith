import { FC } from 'react'
import { useGetGithubPullsQuery } from 'common/services/useGithub'
import PullRequestSelect from './PullRequestSelect'

type MyGithubPullRequestSelectType = {
  organisationId: number
  repoOwner: string
  repoName: string
  onChange: (value: string) => void
}

const MyGithubPullRequests: FC<MyGithubPullRequestSelectType> = ({
  onChange,
  organisationId,
  repoName,
  repoOwner,
}) => {
  const { data } = useGetGithubPullsQuery({
    organisation_id: organisationId,
    repo_name: repoName,
    repo_owner: repoOwner,
  })
  return <PullRequestSelect pullRequest={data} onChange={onChange} />
}

export default MyGithubPullRequests
