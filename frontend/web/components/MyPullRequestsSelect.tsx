import { FC } from 'react'
import { useGetGithubPullsQuery } from 'common/services/useGithub'
import GroupSelect, { GroupSelectType } from './GroupSelect' // we need this to make JSX compile

type MyGithubPullRequestSelectType = {
  orgId: string
}

const MyGithubPullRequest: FC<MyGithubPullsSelectType> = ({ orgId }) => {
  const { data } = useGetGithubPullsQuery({ orgId })
  return <GroupSelect {...props} groups={data?.results} />
}

export default MyGithubPullRequest
