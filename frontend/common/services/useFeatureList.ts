import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Constants from 'common/constants'

export const featureListService = service
  .enhanceEndpoints({
    addTagTypes: ['FeatureList', 'FeatureState', 'MultivariateOption'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMultivariateOption: builder.mutation<
        Res['multivariateOption'],
        Req['createMultivariateOption']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'FeatureList' },
          { id: 'METRICS', type: 'Environment' },
        ],
        query: (query: Req['createMultivariateOption']) => ({
          body: query.body,
          method: 'POST',
          url: `projects/${query.projectId}/features/${query.featureId}/mv-options/`,
        }),
      }),

      deleteMultivariateOption: builder.mutation<
        void,
        Req['deleteMultivariateOption']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'FeatureList' },
          { id: 'METRICS', type: 'Environment' },
        ],
        query: (query: Req['deleteMultivariateOption']) => ({
          method: 'DELETE',
          url: `projects/${query.projectId}/features/${query.featureId}/mv-options/${query.mvId}/`,
        }),
      }),

      getFeatureList: builder.query<Res['featureList'], Req['getFeatureList']>({
        providesTags: (_res, _meta, req) => [
          {
            id: `${req?.projectId}-${req?.environmentId}`,
            type: 'FeatureList',
          },
          { id: 'LIST', type: 'FeatureList' },
        ],
        query: (query: Req['getFeatureList']) => {
          const { environmentId, projectId, ...params } = query
          return {
            params: {
              environment: parseInt(environmentId),
              page: params.page || 1,
              page_size: params.page_size || Constants.FEATURES_PAGE_SIZE,
              ...params,
            },
            url: `projects/${projectId}/features/`,
          }
        },
        transformResponse: (
          response: {
            results: Res['featureList']['results']
            count: number
            next: string | null
            previous: string | null
          },
          _,
          arg,
        ) => ({
          ...response,
          environmentStates: response.results.reduce((acc, feature) => {
            if (feature.environment_feature_state) {
              acc[feature.id] = {
                ...feature.environment_feature_state,
                feature: feature.id,
              }
            }
            return acc
          }, {} as Res['featureList']['environmentStates']),
          pagination: {
            count: response.count,
            currentPage: arg.page || 1,
            next: response.next,
            page: arg.page || 1,
            pageSize: arg.page_size || Constants.FEATURES_PAGE_SIZE,
            previous: response.previous,
          },
        }),
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
        async onQueryStarted(
          { body, environmentId, stateId },
          { dispatch, queryFulfilled },
        ) {
          const patches: { undo: () => void }[] = []

          patches.push(
            dispatch(
              featureListService.util.updateQueryData(
                'getFeatureList',
                (args: Req['getFeatureList']) =>
                  args.environmentId === environmentId,
                (draft) => {
                  const state = Object.values(draft.environmentStates).find(
                    (s) => s.id === stateId,
                  )
                  if (state) {
                    Object.assign(state, body)
                  }
                },
              ),
            ),
          )

          try {
            await queryFulfilled
          } catch (error) {
            patches.forEach((patch) => patch.undo())
          }
        },
        query: (query: Req['updateFeatureState']) => ({
          body: query.body,
          method: 'PUT',
          url: `environments/${query.environmentId}/featurestates/${query.stateId}/`,
        }),
      }),

      updateMultivariateOption: builder.mutation<
        Res['multivariateOption'],
        Req['updateMultivariateOption']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'FeatureList' },
          { id: 'METRICS', type: 'Environment' },
        ],
        query: (query: Req['updateMultivariateOption']) => ({
          body: query.body,
          method: 'PUT',
          url: `projects/${query.projectId}/features/${query.featureId}/mv-options/${query.mvId}/`,
        }),
      }),
    }),
  })

export const {
  useCreateMultivariateOptionMutation,
  useDeleteMultivariateOptionMutation,
  useGetFeatureListQuery,
  useUpdateFeatureStateMutation,
  useUpdateMultivariateOptionMutation,
} = featureListService

export async function getFeatureList(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  store: any,
  data: Req['getFeatureList'],
  options?: Parameters<
    typeof featureListService.endpoints.getFeatureList.initiate
  >[1],
) {
  return store.dispatch(
    featureListService.endpoints.getFeatureList.initiate(data, options),
  )
}
