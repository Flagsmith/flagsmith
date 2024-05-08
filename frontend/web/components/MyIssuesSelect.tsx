import { FC } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'
import IssueSelect from './IssueSelect'

type MyIssuesSelectType = {
  orgId: string
  repoOwner: string
  repoName: string
  onChange: () => void
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({
  onChange,
  orgId,
  repoName,
  repoOwner,
}) => {
  const { data } = useGetGithubIssuesQuery({
    organisation_id: orgId,
    repo_name: repoName,
    repo_owner: repoOwner,
  })
  return <IssueSelect issues={data} onChange={onChange} />
}

export default MyIssuesSelect
