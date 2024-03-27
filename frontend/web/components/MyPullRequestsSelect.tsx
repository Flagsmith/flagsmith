import { FC } from 'react'
import { useGetGithubPullsQuery } from 'common/services/useGithub'
import PullRequestSelect from './PullRequestSelect'

type MyGithubPullRequestSelectType = {
  orgId: string
  onChange: (value: string) => void
}

const MyGithubPullRequests: FC<MyGithubPullRequestSelectType> = ({
  onChange,
  orgId,
}) => {
  const { data } = useGetGithubPullsQuery({ organisation_id: orgId })
  return <PullRequestSelect pullRequest={data} onChange={onChange} />
}

export default MyGithubPullRequests
