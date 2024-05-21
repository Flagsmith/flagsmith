import { createContext, useContext, FC, useEffect, useState } from 'react'
import { useGetGithubIssuesQuery } from 'common/services/useGithub'
import { ExternalResource, Issue, Res } from 'common/types/responses'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'

type IssueSelectProviderType = {
  children: React.ReactNode
  lastSavedResource: string | undefined
  linkedExternalResources: ExternalResource[]
  onChange: (v: string) => void
  orgId: string
  repoOwner: string
  repoName: string
}

type IssueSelectContextType = {
  count: number
  issues?: Issue[]
  isFetching: boolean
  isLoading: boolean
  loadMore: () => void
  loadingCombinedData: boolean
  nextPage?: string
  searchItems: (search: string) => void
}

const IssueSelectContext = createContext<IssueSelectContextType | undefined>(
  undefined,
)

export const IssueSelectProvider: FC<IssueSelectProviderType> = ({
  children,
  ...props
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
      organisation_id: props.orgId,
      page_size: 100,
      repo_name: props.repoName,
      repo_owner: props.repoOwner,
    },
    throttleDelay,
  )

  const { count, next, results } = data || { results: [] }

  useEffect(() => {
    console.log(
      `IsLoading: ${isLoading.toString()} isFetching: ${isFetching.toString()}`,
    )
  }, [isLoading, isFetching])

  useEffect(() => {
    if (results && props.linkedExternalResources) {
      setExternalResourcesSelect(
        results.filter((i: Issue) => {
          const same = props.linkedExternalResources?.some(
            (r) => i.html_url === r.url,
          )
          return !same
        }),
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, props.linkedExternalResources])

  return (
    <IssueSelectContext.Provider
      value={{
        ...props,
        count: count || 0,
        isFetching,
        isLoading,
        issues: externalResourcesSelect,
        loadMore,
        loadingCombinedData,
        nextPage: next,
        searchItems,
      }}
    >
      {children}
    </IssueSelectContext.Provider>
  )
}

export const useIssueSelectProvider = () => {
  const context = useContext(IssueSelectContext)
  if (!context) {
    throw new Error('useIssueSelect must be used within a IssueSelectProvider')
  }
  return context
}
