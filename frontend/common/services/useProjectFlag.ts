import { PagedResponse, ProjectFlag, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import data from 'common/data/base/_data'
import { BaseQueryFn } from '@reduxjs/toolkit/query'
import Utils from 'common/utils/utils'

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
  .enhanceEndpoints({ addTagTypes: ['ProjectFlag'] })
  .injectEndpoints({
    endpoints: (builder) => ({
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
          { id: req?.project, type: 'ProjectFlag' },
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
      // END OF ENDPOINTS
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
// END OF FUNCTION_EXPORTS

export const {
  useGetProjectFlagQuery,
  useGetProjectFlagsQuery,
  // END OF EXPORTS
} = projectFlagService

/* Usage examples:
const { data, isLoading } = useGetProjectFlagsQuery({ id: 2 }, {}) //get hook
const [createProjectFlags, { isLoading, data, isSuccess }] = useCreateProjectFlagsMutation() //create hook
projectFlagService.endpoints.getProjectFlags.select({id: 2})(store.getState()) //access data from any function
*/
