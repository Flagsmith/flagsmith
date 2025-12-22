import { FeatureState, PagedResponse, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import { getFeatureSegment } from './useFeatureSegment'
import { getStore } from 'common/store'
export const addFeatureSegmentsToFeatureStates = async (v) => {
  if (typeof v.feature_segment !== 'number') {
    return v
  }
  const featureSegmentData = await getFeatureSegment(getStore(), {
    id: v.feature_segment,
  })
  return {
    ...v,
    feature_segment: featureSegmentData.data,
  }
}
export const featureStateService = service
  .enhanceEndpoints({
    addTagTypes: ['FeatureState', 'FeatureList', 'Environment'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureStates: builder.query<
        Res['featureStates'],
        Req['getFeatureStates']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureState' }],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          const {
            data,
          }: {
            data: PagedResponse<
              Omit<FeatureState, 'feature_segment'> & {
                feature_segment: number | null
              }
            >
          } = await baseQuery({
            url: `features/featurestates/?${Utils.toParam(query)}`,
          })
          const results = await Promise.all(
            data.results.map(addFeatureSegmentsToFeatureStates),
          )
          return {
            data: {
              ...data,
              results,
            },
          }
        },
      }),
      updateFeatureState: builder.mutation<
        Res['featureState'],
        Req['updateFeatureState']
      >({
        invalidatesTags: (_res, _meta, _req) => [
          { id: 'LIST', type: 'FeatureList' },
          { id: 'LIST', type: 'FeatureState' },
          { id: 'METRICS', type: 'Environment' },
        ],
        query: (query: Req['updateFeatureState']) => ({
          body: query.body,
          method: 'PUT',
          url: `environments/${query.environmentId}/featurestates/${query.environmentFlagId}/`,
        }),
      }),
    }),
  })

export async function getFeatureStates(
  store: any,
  data: Req['getFeatureStates'],
  options?: Parameters<
    typeof featureStateService.endpoints.getFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.getFeatureStates.initiate(data, options),
  )
}

export async function updateFeatureState(
  store: any,
  data: Req['updateFeatureState'],
  options?: Parameters<
    typeof featureStateService.endpoints.updateFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.updateFeatureState.initiate(data, options),
  )
}

export const { useGetFeatureStatesQuery, useUpdateFeatureStateMutation } =
  featureStateService
