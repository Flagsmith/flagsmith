import { FC } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'
import IssueSelect from './IssueSelect'

type MyIssuesSelectType = {
  organisationId: number
  repoOwner: string
  repoName: string
  onChange: () => void
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({
  onChange,
  organisationId,
  repoName,
  repoOwner,
}) => {
  const { data } = useGetGithubIssuesQuery({
    organisation_id: organisationId,
    repo_name: repoName,
    repo_owner: repoOwner,
  })
  return <IssueSelect issues={data} onChange={onChange} />
}

export default MyIssuesSelect
