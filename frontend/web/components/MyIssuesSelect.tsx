import { FC, useEffect, useState } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'
import IssueSelect from './IssueSelect'
import { ExternalResource, Issue } from 'common/types/responses'

type MyIssuesSelectType = {
  orgId: string
  repoOwner: string
  repoName: string
  linkedExternalResources: ExternalResource[]
  onChange: (v: string) => void
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({
  linkedExternalResources,
  onChange,
  orgId,
  repoName,
  repoOwner,
}) => {
  const [extenalResourcesSelect, setExtenalResourcesSelect] =
    useState<Issue[]>()
  const { data } = useGetGithubIssuesQuery({
    organisation_id: orgId,
    repo_name: repoName,
    repo_owner: repoOwner,
  })

  useEffect(() => {
    if (data) {
      setExtenalResourcesSelect(
        data.filter((i: Issue) => {
          const same = linkedExternalResources?.some(
            (r) => i.html_url === r.url,
          )
          return !same
        }),
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  return <IssueSelect issues={extenalResourcesSelect} onChange={onChange} />
}

export default MyIssuesSelect
