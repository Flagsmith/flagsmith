import { MultivariateOption, ProjectFlag, Res } from 'common/types/responses'
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
      saveMultivariateOptions: builder.mutation<
        Res['saveMultivariateOptions'],
        Req['saveMultivariateOptions']
      >({
        invalidatesTags: (res, _, arg) =>
          res && !res.errors
            ? [{ id: arg.feature_id, type: 'ProjectFlag' }]
            : [],
        queryFn: async (args, _, _2, baseQuery) => {
          const featureUrl = `projects/${args.project_id}/features/${args.feature_id}/`
          // Diff against the server's current options rather than any client
          // cache, so stale state can never turn an update into a duplicate
          // create.
          const flagRes = await baseQuery({ method: 'GET', url: featureUrl })
          if (flagRes.error) {
            return { error: flagRes.error }
          }
          const serverOptions =
            (flagRes.data as ProjectFlag)?.multivariate_options || []
          const errors: Record<number, any> = {}
          // Results are written back by input index — downstream feature
          // state saves map weights to option ids positionally.
          const ordered: MultivariateOption[] = []
          await Promise.all(
            args.multivariate_options.map(async (v, i) => {
              let original
              if (v.id) {
                original = serverOptions.find((m) => m.id === v.id)
              } else if (v.key) {
                original = serverOptions.find((m) => !!m.key && m.key === v.key)
              }
              const body = {
                ...v,
                default_percentage_allocation: 0,
                feature: args.feature_id,
              }
              const res = await baseQuery(
                original
                  ? {
                      body,
                      method: 'PUT',
                      url: `${featureUrl}mv-options/${original.id}/`,
                    }
                  : {
                      body,
                      method: 'POST',
                      url: `${featureUrl}mv-options/`,
                    },
              )
              if (res.error) {
                errors[i] = (res.error as { data?: any })?.data ?? null
              } else {
                ordered[i] = res.data as MultivariateOption
              }
            }),
          )
          if (Object.keys(errors).length) {
            return { data: { errors, multivariate_options: ordered } }
          }
          const deleted = serverOptions.filter(
            (m) => !ordered.find((o) => o?.id === m.id),
          )
          const deleteResults = await Promise.all(
            deleted.map((m) =>
              baseQuery({
                method: 'DELETE',
                url: `${featureUrl}mv-options/${m.id}/`,
              }),
            ),
          )
          const failedDelete = deleteResults.find((r) => r.error)
          if (failedDelete) {
            return { error: failedDelete.error }
          }
          return { data: { errors: null, multivariate_options: ordered } }
        },
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

export async function saveMultivariateOptions(
  store: any,
  data: Req['saveMultivariateOptions'],
  options?: Parameters<
    typeof multivariateOptionService.endpoints.saveMultivariateOptions.initiate
  >[1],
) {
  return store.dispatch(
    multivariateOptionService.endpoints.saveMultivariateOptions.initiate(
      data,
      options,
    ),
  )
}

export const {
  useCreateMultivariateOptionMutation,
  useDeleteMultivariateOptionMutation,
  useSaveMultivariateOptionsMutation,
  useUpdateMultivariateOptionMutation,
  // END OF EXPORTS
} = multivariateOptionService
