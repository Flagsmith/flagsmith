import { FC, useEffect, useState } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'
import IssueSelect from './IssueSelect'
import { ExternalResource, Issue, Res } from 'common/types/responses'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'

type MyIssuesSelectType = {
  orgId: string
  repoOwner: string
  repoName: string
  linkedExternalResources: ExternalResource[]
  onChange: (v: string) => void
  resetValue: boolean
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({
  linkedExternalResources,
  onChange,
  orgId,
  repoName,
  repoOwner,
  resetValue,
}) => {
  const [externalResourcesSelect, setExternalResourcesSelect] =
    useState<Issue[]>()

  const { data, isFetching, isLoading, loadMore, searchItems } =
    useInfiniteScroll<Req['getGithubIssues'], Res['githubIssues']>(
      useGetGithubIssuesQuery,
      {
        organisation_id: orgId,
        page_size: 100,
        repo_name: repoName,
        repo_owner: repoOwner,
      },
    )

  const { next, results } = data || { results: [] }

  useEffect(() => {
    if (results && linkedExternalResources) {
      setExternalResourcesSelect(
        results.filter((i: Issue) => {
          const same = linkedExternalResources?.some(
            (r) => i.html_url === r.url,
          )
          return !same
        }),
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, linkedExternalResources])

  return (
    <IssueSelect
      issues={externalResourcesSelect}
      onChange={onChange}
      isFetching={isFetching}
      isLoading={isLoading}
      loadMore={loadMore}
      nextPage={next}
      searchItems={searchItems}
      resetValue={resetValue}
    />
  )
}

export default MyIssuesSelect
