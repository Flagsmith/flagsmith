import React, { FC, useEffect, useRef, useState } from 'react'
import { GithubResources } from 'common/types/responses'
import Utils from 'common/utils/utils'
import { FixedSizeList } from 'react-window'
import InfiniteLoader from 'react-window-infinite-loader'
import { useGitHubResourceSelectProvider } from './GitHubResourceSelectProvider'

type MenuListType = {
  children: React.ReactNode
  searchText: (v: string) => void
  selectProps: any
  width: number
  [key: string]: any
}

const MenuList: FC<MenuListType> = ({
  children,
  searchText,
  selectProps,
  width,
  ...rest
}) => {
  const infiniteLoaderRef = useRef(null)
  const hasMountedRef = useRef(false)
  const childrenArray = React.Children.toArray(children)
  const {
    isFetching,
    isLoading: parentIsLoading,
    loadMore,
    loadingCombinedData,
    nextPage,
  } = useGitHubResourceSelectProvider()
  const [isLoading, setIsLoading] = useState(parentIsLoading)
  const loadMoreItems =
    isFetching || isLoading || !nextPage ? () => {} : loadMore
  const isItemLoaded = (index: number) => childrenArray[index] !== undefined
  const itemCount = childrenArray.length + (nextPage ? 1 : 0)
  const itemSize = 60

  const moreItems = async (
    startIndex: number,
    stopIndex: number,
  ): Promise<void> => {
    return loadMoreItems()
  }

  useEffect(() => {
    setIsLoading(parentIsLoading || loadingCombinedData)
  }, [parentIsLoading, loadingCombinedData])

  useEffect(() => {
    // Reset cached items when "searchText" changes.
    if (hasMountedRef.current) {
      if (infiniteLoaderRef.current) {
        if (loadingCombinedData) {
          ;(
            infiniteLoaderRef.current as InfiniteLoader
          ).resetloadMoreItemsCache()
        }
      }
    }
    hasMountedRef.current = true
  }, [searchText, loadingCombinedData])

  return isLoading ? (
    <div>Loading...</div>
  ) : !itemCount ? (
    <div>No results found</div>
  ) : (
    <InfiniteLoader
      isItemLoaded={isItemLoaded}
      itemCount={itemCount}
      loadMoreItems={moreItems}
      threshold={40}
    >
      {({ onItemsRendered, ref }) => (
        <FixedSizeList
          {...rest}
          height={Math.min(
            itemCount * itemSize + 20,
            selectProps.maxMenuHeight,
          )}
          itemCount={itemCount}
          itemSize={itemSize}
          onItemsRendered={onItemsRendered}
          ref={ref}
          width={width}
        >
          {({ index, isScrolling, style, ...rest }) => {
            const child = childrenArray[index]
            return (
              <div {...rest} style={style}>
                {isItemLoaded(index) ? (
                  child
                ) : (
                  <div className='text-center'>
                    <Loader />
                  </div>
                )}
              </div>
            )
          }}
        </FixedSizeList>
      )}
    </InfiniteLoader>
  )
}

export type GitHubResourcesSelectType = {
  onChange: (value: string) => void
  lastSavedResource: string | undefined
}

type GitHubResourcesValueType = {
  value: string
}

const GitHubResourcesSelect: FC<GitHubResourcesSelectType> = ({
  lastSavedResource,
  onChange,
}) => {
  const {
    githubResources,
    isFetching,
    isLoading,
    loadMore,
    loadingCombinedData,
    nextPage,
    searchItems,
  } = useGitHubResourceSelectProvider()
  const [selectedOption, setSelectedOption] =
    useState<GitHubResourcesValueType | null>(null)
  const [searchText, setSearchText] = React.useState('')

  useEffect(() => {
    if (selectedOption && selectedOption.value === lastSavedResource) {
      setSelectedOption(null)
    }
  }, [lastSavedResource, selectedOption])

  return (
    <div>
      <Select
        filterOption={(options: any[]) => {
          return options
        }}
        value={selectedOption}
        size='select-md'
        placeholder={'Select Your Resource'}
        onChange={(v: GitHubResourcesValueType) => {
          setSelectedOption(v)
          onChange(v?.value)
        }}
        isClearable={true}
        options={githubResources?.map((i: GithubResources) => {
          return {
            label: `${i.title} #${i.number}`,
            status: i.state,
            value: i.html_url,
          }
        })}
        noOptionsMessage={() =>
          isLoading
            ? 'Loading...'
            : isFetching
            ? 'Refreshing data ...'
            : 'No Results found'
        }
        onInputChange={(e: any) => {
          setSearchText(e)
          searchItems(Utils.safeParseEventValue(e))
        }}
        components={{
          MenuList,
        }}
        data={{ searchText }}
      />
    </div>
  )
}

export default GitHubResourcesSelect
