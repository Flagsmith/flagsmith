import React, { FC, useEffect, useRef, useState } from 'react'
import { Issue } from 'common/types/responses'
import Utils from 'common/utils/utils'
import { FixedSizeList } from 'react-window'
import InfiniteLoader from 'react-window-infinite-loader'

const MenuList = (props: any) => {
  const infiniteLoaderRef = useRef(null)
  const hasMountedRef = useRef(false)
  const { children } = props
  const childrenArray = React.Children.toArray(children)
  const {
    isFetching,
    isLoading: parentIsLoading,
    loadMore,
    loadingCombinedData,
    nextPage,
    searchText,
  } = props.selectProps.data
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
          {...props}
          minHeight={props.selectProps.minMenuHeight}
          maxHeight={props.selectProps.maxMenuHeight}
          height={
            Math.min(itemCount * itemSize, props.selectProps.maxMenuHeight) + 20
          }
          itemCount={itemCount}
          itemSize={itemSize}
          onItemsRendered={onItemsRendered}
          ref={ref}
          width={props.width}
        >
          {({ index, isScrolling, style, ...rest }) => {
            const child = childrenArray[index]
            return (
              <div {...rest} style={style}>
                {isItemLoaded(index) ? (
                  child
                ) : (
                  <>
                    <div className='text-center'>
                      <Loader />
                    </div>
                    <div className='text-center'>
                      {itemCount} : {index} : {childrenArray.length}
                    </div>
                  </>
                )}
              </div>
            )
          }}
        </FixedSizeList>
      )}
    </InfiniteLoader>
  )
}

export type IssueSelectType = {
  count: number
  disabled?: boolean
  loadingCombinedData: boolean
  isFetching: boolean
  isLoading: boolean
  issues?: Issue[]
  loadMore: () => void
  nextPage?: string
  onChange: (value: string) => void
  searchItems: (search: string) => void
  lastSavedResource: string | undefined
}

type IssueValueType = {
  value: string
}

const IssueSelect: FC<IssueSelectType> = ({
  count,
  disabled,
  isFetching,
  isLoading,
  issues,
  lastSavedResource,
  loadMore,
  loadingCombinedData,
  nextPage,
  onChange,
  searchItems,
}) => {
  const [selectedOption, setSelectedOption] = useState<IssueValueType | null>(
    null,
  )
  const [searchText, setSearchText] = React.useState('')

  useEffect(() => {
    if (selectedOption && selectedOption.value === lastSavedResource) {
      setSelectedOption(null)
    }
  }, [lastSavedResource, selectedOption])

  return (
    <div style={{ width: '300px' }}>
      <Select
        filterOption={(options: any[]) => {
          return options
        }}
        value={selectedOption}
        size='select-md'
        placeholder={'Select Your Issue'}
        onChange={(v: IssueValueType) => {
          setSelectedOption(v)
          onChange(v?.value)
        }}
        disabled={disabled}
        options={issues?.map((i: Issue) => {
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
            : 'No issues found'
        }
        onInputChange={(e: any) => {
          setSearchText(e)
          searchItems(Utils.safeParseEventValue(e))
        }}
        components={{
          MenuList,
        }}
        data={{
          count,
          isFetching,
          isLoading,
          issues,
          loadMore,
          loadingCombinedData,
          nextPage,
          onChange,
          searchText,
          setSelectedOption,
        }}
      />
    </div>
  )
}

export default IssueSelect
