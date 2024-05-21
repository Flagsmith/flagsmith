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
  lastSavedResource: string | undefined
  linkedExternalResources: ExternalResource[]
  onChange: (v: string) => void
}

const MyIssuesSelect: FC<MyIssuesSelectType> = ({
  lastSavedResource,
  linkedExternalResources,
  onChange,
  orgId,
  repoName,
  repoOwner,
}) => {
  const [externalResourcesSelect, setExternalResourcesSelect] =
    useState<Issue[]>()

  const throttleDelay = 300

  const {
    data,
    isFetching,
    isLoading,
    loadMore,
    loadingCombinedData,
    searchItems,
  } = useInfiniteScroll<Req['getGithubIssues'], Res['githubIssues']>(
    useGetGithubIssuesQuery,
    {
      organisation_id: orgId,
      page_size: 10,
      repo_name: repoName,
      repo_owner: repoOwner,
    },
    throttleDelay,
  )

  const { count, next, results } = data || { results: [] }

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
      count={count || 0}
      issues={externalResourcesSelect}
      onChange={onChange}
      isFetching={isFetching}
      loadingCombinedData={loadingCombinedData}
      isLoading={isLoading}
      lastSavedResource={lastSavedResource}
      loadMore={loadMore}
      nextPage={next}
      searchItems={searchItems}
    />
  )
}

export default MyIssuesSelect
