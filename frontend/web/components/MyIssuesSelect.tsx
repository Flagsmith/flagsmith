import { FC } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'
import IssueSelect from './IssueSelect'

type MyIssuesSelectType = {
  orgId: string
  onChange: () => void
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({ onChange, orgId }) => {
  const { data } = useGetGithubIssuesQuery({ organisation_id: orgId })
  return <IssueSelect issues={data} onChange={onChange} />
}

export default MyIssuesSelect
