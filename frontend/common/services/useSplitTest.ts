import {
  PagedResponse,
  PConfidence,
  Res,
  ServersideSplitTestResult,
  SplitTestResult,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import { groupBy, sortBy } from 'lodash'

export const splitTestService = service
  .enhanceEndpoints({ addTagTypes: ['SplitTest'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getSplitTest: builder.query<Res['splitTest'], Req['getSplitTest']>({
        providesTags: (res, _, q) => [
          { id: q?.conversion_event_type_id, type: 'SplitTest' },
        ],
        query: (query: Req['getSplitTest']) => ({
          url: `split-testing/?${Utils.toParam(query)}`,
        }),
        transformResponse: (res: PagedResponse<ServersideSplitTestResult>) => {
          const groupedFeatures = groupBy(
            res.results,
            (item) => item.feature.id,
          )

          const results: SplitTestResult[] = Object.keys(groupedFeatures).map(
            (group) => {
              const features = groupedFeatures[group]
              let minP = Number.MAX_SAFE_INTEGER
              let maxP = Number.MIN_SAFE_INTEGER
              let maxConversionCount = Number.MIN_SAFE_INTEGER
              let maxConversionPercentage = Number.MIN_SAFE_INTEGER
              let minConversion = Number.MAX_SAFE_INTEGER
              let maxConversionPValue = 0
              const results = sortBy(
                features.map((v) => {
                  if (v.pvalue < minP) {
                    minP = v.pvalue
                  }
                  if (v.pvalue > maxP) {
                    maxP = v.pvalue
                  }
                  const conversion = v.conversion_count
                    ? Math.round(
                        (v.conversion_count / v.evaluation_count) * 100,
                      )
                    : 0
                  if (conversion > maxConversionPercentage) {
                    maxConversionCount = v.conversion_count
                    maxConversionPercentage = conversion
                    maxConversionPValue = v.pvalue
                  }
                  if (conversion < minConversion) {
                    minConversion = conversion
                  }

                  return {
                    confidence: Utils.convertToPConfidence(v.pvalue),
                    conversion_count: v.conversion_count,
                    conversion_percentage: conversion,
                    evaluation_count: v.evaluation_count,
                    pvalue: v.pvalue,
                    value_data: v.value_data,
                  } as SplitTestResult['results'][number]
                }),
                'conversion_count',
              )
              return {
                conversion_variance: maxConversionPercentage - minConversion,
                feature: features[0].feature,
                max_conversion_count: maxConversionCount,
                max_conversion_percentage: maxConversionPercentage,
                max_conversion_pvalue: maxConversionPValue,
                results: sortBy(results, (v) => -v.conversion_count),
              }
            },
          )
          return {
            ...res,
            results,
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getSplitTest(
  store: any,
  data: Req['getSplitTest'],
  options?: Parameters<
    typeof splitTestService.endpoints.getSplitTest.initiate
  >[1],
) {
  return store.dispatch(
    splitTestService.endpoints.getSplitTest.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetSplitTestQuery,
  // END OF EXPORTS
} = splitTestService

/* Usage examples:
const { data, isLoading } = useGetSplitTestQuery({ id: 2 }, {}) //get hook
const [createSplitTest, { isLoading, data, isSuccess }] = useCreateSplitTestMutation() //create hook
splitTestService.endpoints.getSplitTest.select({id: 2})(store.getState()) //access data from any function
*/
