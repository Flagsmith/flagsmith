import { FC } from 'react'
import { useGetGithubPullsQuery } from 'common/services/useGithub'
import PullRequestSelect from './PullRequestSelect'

type MyGithubPullRequestSelectType = {
  orgId: string
  repoOwner: string
  repoName: string
  onChange: (value: string) => void
}

const MyGithubPullRequests: FC<MyGithubPullRequestSelectType> = ({
  onChange,
  orgId,
  repoName,
  repoOwner,
}) => {
  const { data } = useGetGithubPullsQuery({
    organisation_id: orgId,
    repo_name: repoName,
    repo_owner: repoOwner,
  })
  return <PullRequestSelect pullRequest={data} onChange={onChange} />
}

export default MyGithubPullRequests
