import { FC } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'

type MyIssuesSelectType = {
  orgId: string
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({ orgId }) => {
  const { data } = useGetGithubIssuesQuery({ orgId })
  // return <GroupSelect {...props} groups={data?.results} />
}

export default MyIssuesSelect
