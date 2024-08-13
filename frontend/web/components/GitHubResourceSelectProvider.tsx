import { createContext, useContext, FC, useEffect, useState } from 'react'
import { useGetGithubResourcesQuery } from 'common/services/useGithub'
import { ExternalResource, GithubResource, Res } from 'common/types/responses'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'

type GitHubResourceSelectProviderType = {
  children: React.ReactNode
  githubResource: string
  lastSavedResource: string | undefined
  linkedExternalResources: ExternalResource[]
  onChange: (v: string) => void
  orgId: string
  repoOwner: string
  repoName: string
}

type GitHubResourceSelectContextType = {
  count: number
  githubResources?: GithubResource[]
  isFetching: boolean
  isLoading: boolean
  loadMore: () => void
  loadingCombinedData: boolean
  nextPage?: string
  searchItems: (search: string) => void
  refresh: () => void
}

const GitHubResourceSelectContext = createContext<
  GitHubResourceSelectContextType | undefined
>(undefined)

export const GitHubResourceSelectProvider: FC<
  GitHubResourceSelectProviderType
> = ({ children, ...props }) => {
  const [externalResourcesSelect, setExternalResourcesSelect] =
    useState<GithubResource[]>()

  const throttleDelay = 300

  const {
    data,
    isFetching,
    isLoading,
    loadMore,
    loadingCombinedData,
    refresh,
    searchItems,
  } = useInfiniteScroll<Req['getGithubResources'], Res['githubResources']>(
    useGetGithubResourcesQuery,
    {
      github_resource: props.githubResource,
      organisation_id: props.orgId,
      page_size: 100,
      repo_name: props.repoName,
      repo_owner: props.repoOwner,
    },
    throttleDelay,
  )

  const { count, next, results } = data || { results: [] }

  useEffect(() => {
    if (results && props.linkedExternalResources) {
      setExternalResourcesSelect(
        results.filter((i: GithubResource) => {
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
    <GitHubResourceSelectContext.Provider
      value={{
        ...props,
        count: count || 0,
        githubResources: externalResourcesSelect,
        isFetching,
        isLoading,
        loadMore,
        loadingCombinedData,
        nextPage: next,
        refresh,
        searchItems,
      }}
    >
      {children}
    </GitHubResourceSelectContext.Provider>
  )
}

export const useGitHubResourceSelectProvider = () => {
  const context = useContext(GitHubResourceSelectContext)
  if (!context) {
    throw new Error(
      'useGitHubResourceSelect must be used within a GitHubResourceSelectProvider',
    )
  }
  return context
}
