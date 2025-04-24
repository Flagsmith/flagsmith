import { UseQuery } from '@reduxjs/toolkit/dist/query/react/buildHooks'
import { useCallback, useEffect, useState } from 'react'
import { PagedRequest } from './types/requests'
import { PagedResponse } from './types/responses'
import { QueryDefinition } from '@reduxjs/toolkit/query'
import useThrottle from './useThrottle'
import { SubscriptionOptions } from '@reduxjs/toolkit/src/query/core/apiState'

const useInfiniteScroll = <
  REQ extends PagedRequest<{}>,
  RES extends PagedResponse<{}>,
>(
  useGetDataListQuery: UseQuery<QueryDefinition<REQ, any, any, RES>>,
  queryParameters: REQ,
  throttle = 500,
  queryOptions?: SubscriptionOptions & {
    skip?: boolean
    refetchOnMountOrArgChange?: boolean | number
  },
) => {
  const [localPage, setLocalPage] = useState(1)
  const [combinedData, setCombinedData] = useState<RES | null>(null)
  const [loadingCombinedData, setLoadingCombinedData] = useState(false)
  const [q, setQ] = useState('')

  const queryResponse = useGetDataListQuery(
    {
      ...queryParameters,
      page: localPage,
      q,
    },
    queryOptions,
  )

  useEffect(
    () => {
      if (queryResponse?.data) {
        if (queryResponse.originalArgs?.page === 1) {
          setCombinedData(queryResponse?.data)
        } else {
          // This is a new page, combine the data
          setCombinedData((prev) => {
            return {
              ...queryResponse.data,
              results: prev?.results
                ? prev.results.concat(queryResponse.data?.results || [])
                : queryResponse.data?.results,
            } as RES
          })
        }
        setLoadingCombinedData(false)
      }
    }, //eslint-disable-next-line
        [queryResponse?.data]
  )

  const searchItems = useThrottle((search: string) => {
    if (q !== search) {
      setLoadingCombinedData(true)
    }
    setQ(search)
    setLocalPage(1)
  }, throttle)

  const refresh = useCallback(() => {
    queryResponse.refetch().then((newData) => {
      setCombinedData(newData as unknown as RES)
      setLocalPage(1)
    })
  }, [queryResponse])

  const loadMore = () => {
    if (queryResponse?.data?.next) {
      setLocalPage((page) => page + 1)
    }
  }

  return {
    data: combinedData,
    isFetching: queryResponse.isFetching,
    isLoading: queryResponse.isLoading,
    loadMore,
    loadingCombinedData: loadingCombinedData && queryResponse.isFetching,
    // refetchData,
    refresh,
    response: queryResponse,
    searchItems,
  }
}

export default useInfiniteScroll
/*  Usage example:
const {data, isLoading, searchItems, loadMore} =
useInfiniteScroll<Req['getX'], Res['x']>(useGetXQuery, { page_size:10, otherParam:"test" })
*/
