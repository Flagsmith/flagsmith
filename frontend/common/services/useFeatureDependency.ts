import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import { service } from 'common/service'

type DependencyTag = { id: string; type: 'FeatureDependency' }

// Adding and removing a prerequisite take the same arguments.
type DependencyQuery = Req['createFeatureDependency']

const listTags = (query: {
  environmentId: string
  featureId: number
}): DependencyTag[] => [
  {
    id: `${query.environmentId}-${query.featureId}`,
    type: 'FeatureDependency',
  },
  // Also claim the environment-wide tag, so a write against any feature
  // refreshes every dependency list in that environment.
  { id: `LIST-${query.environmentId}`, type: 'FeatureDependency' },
]

// Adding or removing a prerequisite changes what both features report, so a
// write has to clear every dependency list for the environment.
const invalidateEnvironment = (query: {
  environmentId: string
}): DependencyTag[] => [
  { id: `LIST-${query.environmentId}`, type: 'FeatureDependency' },
]

// With a change request, the API stages the change in it, or lists the
// dependencies as if it were live.
const withChangeRequest = (url: string, changeRequestId?: number) =>
  changeRequestId ? `${url}?change_request=${changeRequestId}` : url

const dependencyUrl = (query: DependencyQuery) =>
  withChangeRequest(
    `environments/${query.environmentId}/features/${query.featureId}/dependencies/${query.prerequisiteFeatureId}/`,
    query.changeRequestId,
  )

const pendingTags = (featureId: number): DependencyTag[] => [
  { id: `PENDING-${featureId}`, type: 'FeatureDependency' },
  { id: 'PENDING', type: 'FeatureDependency' },
]

export const featureDependencyService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureDependency'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createFeatureDependency: builder.mutation<
        Res['featureDependency'],
        Req['createFeatureDependency']
      >({
        // A staged change is not live, so only the pending lists change.
        invalidatesTags: (res, err, query) =>
          query.changeRequestId
            ? pendingTags(query.featureId)
            : invalidateEnvironment(query),
        // The POST answers with the edge, so the row need not wait on the
        // refetch the invalidation triggers.
        onQueryStarted: async (query, { dispatch, queryFulfilled }) => {
          if (query.changeRequestId) return
          let edge: Res['featureDependency']
          try {
            edge = (await queryFulfilled).data
          } catch {
            // Refused; the caller reports it. Uncaught it would surface twice.
            return
          }
          dispatch(
            featureDependencyService.util.updateQueryData(
              'getFeatureDependencies',
              {
                environmentId: query.environmentId,
                featureId: query.featureId,
              },
              (draft) => {
                // The refetch may have landed first.
                if (draft.results.some((e) => e.segment.id === edge.segment.id))
                  return
                draft.results.push(edge)
              },
            ),
          )
        },
        query: (query: Req['createFeatureDependency']) => ({
          method: 'POST',
          url: dependencyUrl(query),
        }),
      }),
      deleteFeatureDependency: builder.mutation<
        void,
        Req['deleteFeatureDependency']
      >({
        invalidatesTags: (res, err, query) =>
          query.changeRequestId
            ? pendingTags(query.featureId)
            : invalidateEnvironment(query),
        query: (query: Req['deleteFeatureDependency']) => ({
          method: 'DELETE',
          url: dependencyUrl(query),
        }),
      }),
      getFeatureDependencies: builder.query<
        Res['featureDependencies'],
        Req['getFeatureDependencies']
      >({
        providesTags: (res, err, query) => [
          ...listTags(query),
          ...(query.changeRequestId ? pendingTags(query.featureId) : []),
        ],
        query: (query: Req['getFeatureDependencies']) => ({
          url: withChangeRequest(
            `environments/${query.environmentId}/features/${query.featureId}/dependencies/`,
            query.changeRequestId,
          ),
        }),
      }),

      getFeatureDependents: builder.query<
        Res['featureDependents'],
        Req['getFeatureDependents']
      >({
        providesTags: (res, err, query) => listTags(query),
        query: (query: Req['getFeatureDependents']) => ({
          url: `environments/${query.environmentId}/features/${query.featureId}/dependents/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createFeatureDependency(
  store: any,
  data: Req['createFeatureDependency'],
  options?: Parameters<
    typeof featureDependencyService.endpoints.createFeatureDependency.initiate
  >[1],
) {
  return store.dispatch(
    featureDependencyService.endpoints.createFeatureDependency.initiate(
      data,
      options,
    ),
  )
}
export async function deleteFeatureDependency(
  store: any,
  data: Req['deleteFeatureDependency'],
  options?: Parameters<
    typeof featureDependencyService.endpoints.deleteFeatureDependency.initiate
  >[1],
) {
  return store.dispatch(
    featureDependencyService.endpoints.deleteFeatureDependency.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureDependencies(
  store: any,
  data: Req['getFeatureDependencies'],
  options?: Parameters<
    typeof featureDependencyService.endpoints.getFeatureDependencies.initiate
  >[1],
) {
  return store.dispatch(
    featureDependencyService.endpoints.getFeatureDependencies.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureDependents(
  store: any,
  data: Req['getFeatureDependents'],
  options?: Parameters<
    typeof featureDependencyService.endpoints.getFeatureDependents.initiate
  >[1],
) {
  return store.dispatch(
    featureDependencyService.endpoints.getFeatureDependents.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateFeatureDependencyMutation,
  useDeleteFeatureDependencyMutation,
  useGetFeatureDependenciesQuery,
  useGetFeatureDependentsQuery,
  // END OF EXPORTS
} = featureDependencyService

/* Usage examples:
const { data, isLoading } = useGetFeatureDependenciesQuery({ environmentId: 'abc', featureId: 2 }, {}) //get hook
const [createFeatureDependency, { isLoading, data, isSuccess }] = useCreateFeatureDependencyMutation() //create hook
featureDependencyService.endpoints.getFeatureDependencies.select({ environmentId: 'abc', featureId: 2 })(store.getState()) //access data from any function
*/
