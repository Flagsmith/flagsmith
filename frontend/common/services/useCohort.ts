import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import toFormData from 'common/utils/toFormData'

export const cohortService = service
  .enhanceEndpoints({ addTagTypes: ['Cohort', 'Segment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createCohort: builder.mutation<Res['cohort'], Req['createCohort']>({
        invalidatesTags: (q, e, arg) => [
          { id: 'LIST', type: 'Cohort' },
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        query: (query) => ({
          body: {
            description: query.description,
            metadata: query.metadata,
            name: query.name,
          },
          method: 'POST',
          url: `environments/${query.environmentApiKey}/cohorts/`,
        }),
      }),
      deleteCohort: builder.mutation<void, Req['deleteCohort']>({
        invalidatesTags: (q, e, arg) => [
          { id: 'LIST', type: 'Cohort' },
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        query: (query) => ({
          method: 'DELETE',
          url: `environments/${query.environmentApiKey}/cohorts/${query.cohortId}/`,
        }),
      }),
      syncCohortCsv: builder.mutation<
        Res['cohortCsvSync'],
        Req['syncCohortCsv']
      >({
        invalidatesTags: (q, e, arg) => [
          { id: arg.cohortId, type: 'Cohort' },
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          // projectId only feeds tag invalidation; keep it out of the form data.
          const { cohortId, environmentApiKey, projectId: _, ...rest } = query
          const formData = toFormData({ ...rest })
          const { data, error } = await baseQuery({
            body: formData,
            method: 'POST',
            url: `environments/${environmentApiKey}/cohorts/${cohortId}/sync-csv/`,
          })
          return { data, error } as {
            data: Res['cohortCsvSync']
            error: never
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function deleteCohort(
  store: any,
  data: Req['deleteCohort'],
  options?: Parameters<typeof cohortService.endpoints.deleteCohort.initiate>[1],
) {
  return store.dispatch(
    cohortService.endpoints.deleteCohort.initiate(data, options),
  )
}

export const {
  useCreateCohortMutation,
  useDeleteCohortMutation,
  useSyncCohortCsvMutation,
  // END OF EXPORTS
} = cohortService

/* Usage examples:
const [createCohort, { isLoading, data, isSuccess }] = useCreateCohortMutation()
const [syncCohortCsv, { isLoading }] = useSyncCohortCsvMutation()
*/
