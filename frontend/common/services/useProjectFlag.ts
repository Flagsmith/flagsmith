import { PagedResponse, ProjectFlag, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

/**
 * Number of features to display per page in the features list.
 */
export const FEATURES_PAGE_SIZE = 50

function recursivePageGet(
  url: string,
  parentRes: null | PagedResponse<ProjectFlag>,
  baseQuery: (arg: unknown) => any, // matches rtk types,
) {
  return baseQuery({
    method: 'GET',
    url,
  }).then((res: Res['projectFlags']) => {
    let response
    if (parentRes) {
      response = {
        ...parentRes,
        results: parentRes.results.concat(res.results),
      }
    } else {
      response = res
    }
    if (res.next) {
      return recursivePageGet(res.next, response, baseQuery)
    }
    return Promise.resolve(response)
  })
}
export const projectFlagService = service
  .enhanceEndpoints({
    addTagTypes: ['ProjectFlag', 'FeatureList', 'FeatureState', 'Environment'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      addFlagGroupOwners: builder.mutation<
        Res['projectFlag'],
        Req['addFlagGroupOwners']
      >({
        invalidatesTags: (res) => [{ id: res?.id, type: 'ProjectFlag' }],
        query: ({ feature_id, project_id, ...body }) => ({
          body,
          method: 'POST',
          url: `projects/${project_id}/features/${feature_id}/add-group-owners/`,
        }),
      }),
      addFlagOwners: builder.mutation<Res['projectFlag'], Req['addFlagOwners']>(
        {
          invalidatesTags: (res) => [{ id: res?.id, type: 'ProjectFlag' }],
          query: ({ feature_id, project_id, ...body }) => ({
            body,
            method: 'POST',
            url: `projects/${project_id}/features/${feature_id}/add-owners/`,
          }),
        },
      ),

      createProjectFlag: builder.mutation<
        Res['projectFlag'],
        Req['createProjectFlag']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'ProjectFlag' },
          { id: 'LIST', type: 'FeatureList' },
        ],
        query: (query: Req['createProjectFlag']) => ({
          body: query.body,
          method: 'POST',
          url: `projects/${query.project_id}/features/`,
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
              ...params,
              environment: parseInt(environmentId),
              page: params.page || 1,
              page_size: params.page_size || FEATURES_PAGE_SIZE,
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
            pageSize: arg.page_size || FEATURES_PAGE_SIZE,
            previous: response.previous,
          },
        }),
      }),

      getProjectFlag: builder.query<Res['projectFlag'], Req['getProjectFlag']>({
        providesTags: (res) => [{ id: res?.id, type: 'ProjectFlag' }],
        query: (query: Req['getProjectFlag']) => ({
          url: `projects/${query.project}/features/${query.id}/`,
        }),
      }),

      getProjectFlags: builder.query<
        Res['projectFlags'],
        Req['getProjectFlags']
      >({
        providesTags: (res, _, req) => [
          {
            id: [req?.project, req?.environment, req?.segment]
              .filter(Boolean)
              .join('-'),
            type: 'ProjectFlag',
          },
        ],
        queryFn: async (args, _, _2, baseQuery) => {
          return await recursivePageGet(
            `projects/${args.project}/features/?${Utils.toParam({
              ...args,
              page_size: 999,
            })}`,
            null,
            baseQuery,
          )
        },
      }),

      removeFlagGroupOwners: builder.mutation<
        Res['projectFlag'],
        Req['removeFlagGroupOwners']
      >({
        invalidatesTags: (res) => [{ id: res?.id, type: 'ProjectFlag' }],
        query: ({ feature_id, project_id, ...body }) => ({
          body,
          method: 'POST',
          url: `projects/${project_id}/features/${feature_id}/remove-group-owners/`,
        }),
      }),

      removeFlagOwners: builder.mutation<
        Res['projectFlag'],
        Req['removeFlagOwners']
      >({
        invalidatesTags: (res) => [{ id: res?.id, type: 'ProjectFlag' }],
        query: ({ feature_id, project_id, ...body }) => ({
          body,
          method: 'POST',
          url: `projects/${project_id}/features/${feature_id}/remove-owners/`,
        }),
      }),

      removeProjectFlag: builder.mutation<void, Req['removeProjectFlag']>({
        invalidatesTags: [
          { id: 'LIST', type: 'ProjectFlag' },
          { id: 'LIST', type: 'FeatureList' },
          { id: 'METRICS', type: 'Environment' },
        ],
        query: ({ flag_id, project_id }) => ({
          method: 'DELETE',
          url: `projects/${project_id}/features/${flag_id}/`,
        }),
      }),

      updateProjectFlag: builder.mutation<
        Res['projectFlag'],
        Req['updateProjectFlag']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'ProjectFlag' },
          { id: res?.id, type: 'ProjectFlag' },
        ],
        query: (query: Req['updateProjectFlag']) => ({
          body: query.body,
          method: 'PUT',
          url: `projects/${query.project_id}/features/${query.feature_id}/`,
        }),
      }),
    }),
  })

export async function getProjectFlags(
  store: any,
  data: Req['getProjectFlags'],
  options?: Parameters<
    typeof projectFlagService.endpoints.getProjectFlags.initiate
  >[1],
) {
  return store.dispatch(
    projectFlagService.endpoints.getProjectFlags.initiate(data, options),
  )
}
export async function getProjectFlag(
  store: any,
  data: Req['getProjectFlag'],
  options?: Parameters<
    typeof projectFlagService.endpoints.getProjectFlag.initiate
  >[1],
) {
  return store.dispatch(
    projectFlagService.endpoints.getProjectFlag.initiate(data, options),
  )
}
export async function updateProjectFlag(
  store: any,
  data: Req['updateProjectFlag'],
  options?: Parameters<
    typeof projectFlagService.endpoints.updateProjectFlag.initiate
  >[1],
) {
  return store.dispatch(
    projectFlagService.endpoints.updateProjectFlag.initiate(data, options),
  )
}
export async function createProjectFlag(
  store: any,
  data: Req['createProjectFlag'],
  options?: Parameters<
    typeof projectFlagService.endpoints.createProjectFlag.initiate
  >[1],
) {
  return store.dispatch(
    projectFlagService.endpoints.createProjectFlag.initiate(data, options),
  )
}
export async function removeProjectFlag(
  store: any,
  data: Req['removeProjectFlag'],
  options?: Parameters<
    typeof projectFlagService.endpoints.removeProjectFlag.initiate
  >[1],
) {
  return store.dispatch(
    projectFlagService.endpoints.removeProjectFlag.initiate(data, options),
  )
}

export const {
  useAddFlagGroupOwnersMutation,
  useAddFlagOwnersMutation,
  useCreateProjectFlagMutation,
  useGetFeatureListQuery,
  useGetProjectFlagQuery,
  useGetProjectFlagsQuery,
  useRemoveFlagGroupOwnersMutation,
  useRemoveFlagOwnersMutation,
  useRemoveProjectFlagMutation,
  useUpdateProjectFlagMutation,
} = projectFlagService
