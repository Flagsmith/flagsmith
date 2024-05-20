import { FC, useEffect, useState } from 'react'
import { useGetGithubPullsQuery } from 'common/services/useGithub'
import PullRequestSelect from './PullRequestSelect'
import { ExternalResource, PullRequest, Res } from 'common/types/responses'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'

type MyGithubPullRequestSelectType = {
  orgId: string
  repoOwner: string
  repoName: string
  onChange: (value: string) => void
  linkedExternalResources: ExternalResource[]
  resetValue: boolean
}

const MyGithubPullRequests: FC<MyGithubPullRequestSelectType> = ({
  linkedExternalResources,
  onChange,
  orgId,
  repoName,
  repoOwner,
  resetValue,
}) => {
  const [externalResourcesSelect, setExternalResourcesSelect] =
    useState<PullRequest[]>()

  const { data, isFetching, isLoading, loadMore, searchItems } =
    useInfiniteScroll<Req['getGithubPulls'], Res['githubPulls']>(
      useGetGithubPullsQuery,
      {
        organisation_id: orgId,
        page_size: 100,
        repo_name: repoName,
        repo_owner: repoOwner,
      },
    )

  const { next, results } = data || { results: [] }

  useEffect(() => {
    console.log(
      `IsLoading: ${isLoading.toString()} isFetching: ${isFetching.toString()}`,
    )
  }, [isLoading, isFetching])

  useEffect(() => {
    if (results && linkedExternalResources) {
      setExternalResourcesSelect(
        results.filter((pr: PullRequest) => {
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
      pullRequest={externalResourcesSelect!}
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

export default MyGithubPullRequests
