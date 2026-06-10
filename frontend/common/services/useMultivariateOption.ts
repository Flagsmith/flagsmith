import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const multivariateOptionService = service
  .enhanceEndpoints({ addTagTypes: ['ProjectFlag'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMultivariateOption: builder.mutation<
        Res['multivariateOption'],
        Req['createMultivariateOption']
      >({
        query: (query) => ({
          body: query.body,
          method: 'POST',
          url: `projects/${query.project_id}/features/${query.feature_id}/mv-options/`,
        }),
      }),
      deleteMultivariateOption: builder.mutation<
        void,
        Req['deleteMultivariateOption']
      >({
        query: (query) => ({
          method: 'DELETE',
          url: `projects/${query.project_id}/features/${query.feature_id}/mv-options/${query.mv_id}/`,
        }),
      }),
      updateMultivariateOption: builder.mutation<
        Res['multivariateOption'],
        Req['updateMultivariateOption']
      >({
        query: (query) => ({
          body: query.body,
          method: 'PUT',
          url: `projects/${query.project_id}/features/${query.feature_id}/mv-options/${query.mv_id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createMultivariateOption(
  store: any,
  data: Req['createMultivariateOption'],
  options?: Parameters<
    typeof multivariateOptionService.endpoints.createMultivariateOption.initiate
  >[1],
) {
  return store.dispatch(
    multivariateOptionService.endpoints.createMultivariateOption.initiate(
      data,
      options,
    ),
  )
}
export async function updateMultivariateOption(
  store: any,
  data: Req['updateMultivariateOption'],
  options?: Parameters<
    typeof multivariateOptionService.endpoints.updateMultivariateOption.initiate
  >[1],
) {
  return store.dispatch(
    multivariateOptionService.endpoints.updateMultivariateOption.initiate(
      data,
      options,
    ),
  )
}
export async function deleteMultivariateOption(
  store: any,
  data: Req['deleteMultivariateOption'],
  options?: Parameters<
    typeof multivariateOptionService.endpoints.deleteMultivariateOption.initiate
  >[1],
) {
  return store.dispatch(
    multivariateOptionService.endpoints.deleteMultivariateOption.initiate(
      data,
      options,
    ),
  )
}

export const {
  useCreateMultivariateOptionMutation,
  useDeleteMultivariateOptionMutation,
  useUpdateMultivariateOptionMutation,
  // END OF EXPORTS
} = multivariateOptionService
