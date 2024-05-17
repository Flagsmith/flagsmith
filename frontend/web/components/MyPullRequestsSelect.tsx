import { FC, useEffect, useState } from 'react'
import { useGetGithubPullsQuery } from 'common/services/useGithub'
import PullRequestSelect from './PullRequestSelect'
import { ExternalResource, PullRequest } from 'common/types/responses'

type MyGithubPullRequestSelectType = {
  orgId: string
  repoOwner: string
  repoName: string
  onChange: (value: string) => void
  linkedExternalResources: ExternalResource[]
}

const MyGithubPullRequests: FC<MyGithubPullRequestSelectType> = ({
  linkedExternalResources,
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
  const [extenalResourcesSelect, setExtenalResourcesSelect] =
    useState<PullRequest[]>()

  useEffect(() => {
    if (data && linkedExternalResources) {
      setExtenalResourcesSelect(
        data.filter((pr: PullRequest) => {
          const same = linkedExternalResources?.some(
            (r) => pr.html_url === r.url,
          )
          return !same
        }),
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, linkedExternalResources])
  return (
    <PullRequestSelect
      pullRequest={extenalResourcesSelect}
      onChange={onChange}
    />
  )
}

export default MyGithubPullRequests
