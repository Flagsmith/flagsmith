import {
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
        // query: (query: Req['getSplitTest']) => ({
        //   url: `split-testing/${Utils.toParam(query)}`,
        // }),
        queryFn: () => {
          const response: ServersideSplitTestResult[] = [
            {
              'conversion_count': 12,
              'evaluation_count': 123,
              'feature': {
                'created_date': '2024-01-31T19:59:33.052928Z',
                'default_enabled': true,
                'description': null,
                'id': 4,
                'initial_value': 'feature',
                'name': 'single_feature_for_test',
                'type': 'MULTIVARIATE',
              },
              'pvalue': 0.2,
              'value_data': {
                'boolean_value': null,
                'integer_value': null,
                'string_value': 'feature',
                'type': 'unicode',
              },
            },
            {
              'conversion_count': 10,
              'evaluation_count': 100,
              'feature': {
                'created_date': '2024-01-31T19:59:33.052928Z',
                'default_enabled': true,
                'description': null,
                'id': 4,
                'initial_value': 'feature',
                'name': 'single_feature_for_test',
                'type': 'MULTIVARIATE',
              },
              'pvalue': 0.2,
              'value_data': {
                'boolean_value': null,
                'integer_value': null,
                'string_value': 'mv_feature_option1',
                'type': 'unicode',
              },
            },
            {
              'conversion_count': 18,
              'evaluation_count': 111,
              'feature': {
                'created_date': '2024-01-31T19:59:33.052928Z',
                'default_enabled': true,
                'description': null,
                'id': 4,
                'initial_value': 'feature',
                'name': 'single_feature_for_test',
                'type': 'MULTIVARIATE',
              },
              'pvalue': 0.2,
              'value_data': {
                'boolean_value': null,
                'integer_value': null,
                'string_value': 'mv_feature_option2',
                'type': 'unicode',
              },
            },
          ]
          const groupedFeatures = groupBy(response, (item) => item.feature.id)

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
            data: {
              count: 3,
              next: null,
              previous: null,
              results,
            },
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
