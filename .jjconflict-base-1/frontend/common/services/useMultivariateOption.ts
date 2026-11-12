import { MultivariateOption, ProjectFlag, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const multivariateOptionService = service.injectEndpoints({
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
    saveMultivariateOptions: builder.mutation<
      Res['saveMultivariateOptions'],
      Req['saveMultivariateOptions']
    >({
      // No invalidatesTags: every save chain already ends with a broad
      // invalidateTags(['ProjectFlag', 'FeatureList']) once the downstream
      // feature-state save completes — invalidating here too would refetch
      // every subscribed query twice per save.
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
        // state saves map weights to option ids positionally. Requests run
        // sequentially so newly created options get ascending ids in input
        // order, which is the order the UI displays.
        const ordered: MultivariateOption[] = []
        for (let i = 0; i < args.multivariate_options.length; i++) {
          const v = args.multivariate_options[i]
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
        }
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
  useSaveMultivariateOptionsMutation,
  // END OF EXPORTS
} = multivariateOptionService
