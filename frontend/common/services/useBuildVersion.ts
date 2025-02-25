import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

import { Version } from 'common/types/responses'
import Project from 'common/project'
import { service } from 'path/to/your/service' // adjust the import as needed

export const buildVersionService = service
  .enhanceEndpoints({ addTagTypes: ['BuildVersion'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getBuildVersion: builder.query<Version, void>({
        providesTags: (res) => [{ id: 'BuildVersion', type: 'BuildVersion' }],
        queryFn: async (args, _, _2, baseQuery) => {
          // Fire both requests concurrently
          const [frontendRes, backendRes] = await Promise.all([
            baseQuery('/version').then((res) => {}),
            baseQuery(`${Project.api.replace('api/v1/', '')}version`),
          ])

          // Check for errors in either fetch
          if (frontendRes.error || backendRes.error) {
            return { error: frontendRes.error || backendRes.error }
          }

          // Cast the responses to the expected types
          const frontend =
            (frontendRes.data as Version['frontend']) ||
            ({} as Version['frontend'])
          const backend =
            (backendRes.data as Version['backend']) ||
            ({} as Version['backend'])

          // Compute additional version properties
          const tag = backend?.image_tag || 'Unknown'
          const backend_sha = backend?.ci_commit_sha || 'Unknown'
          const frontend_sha = frontend?.ci_commit_sha || 'Unknown'

          // Assemble the final version object
          const result: Version = {
            backend,
            backend_sha,
            frontend,
            frontend_sha,
            tag,
          }

          // Make the version globally accessible as before
          global.flagsmithVersion = result

          return { data: result }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export const hasEmailProvider = (version?: Version): boolean =>
  version?.backend?.has_email_provider ?? false

export async function getBuildVersion(
  store: any,
  data: Req['getBuildVersion'],
  options?: Parameters<
    typeof buildVersionService.endpoints.getBuildVersion.initiate
  >[1],
) {
  return store.dispatch(
    buildVersionService.endpoints.getBuildVersion.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetBuildVersionQuery,
  // END OF EXPORTS
} = buildVersionService

/* Usage examples:
const { data, isLoading } = useGetBuildVersionQuery({ id: 2 }, {}) //get hook
const [createBuildVersion, { isLoading, data, isSuccess }] = useCreateBuildVersionMutation() //create hook
buildVersionService.endpoints.getBuildVersion.select({id: 2})(store.getState()) //access data from any function
*/
