import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const integrationService = service
  .enhanceEndpoints({ addTagTypes: ['Integration'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getIntegration: builder.query<Res['integration'], Req['getIntegration']>({
        providesTags: (
          _res,
          _err,
          { environmentId, integrationId, projectId },
        ) => [
          {
            id: `${integrationId}:${projectId ?? ''}:${environmentId ?? ''}`,
            type: 'Integration',
          },
        ],
        query: ({ environmentId, integrationId, projectId }) => {
          if (environmentId) {
            return {
              url: `environments/${environmentId}/integrations/${integrationId}/`,
            }
          }
          return {
            url: `projects/${projectId}/integrations/${integrationId}/`,
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useGetIntegrationQuery,
  // END OF EXPORTS
} = integrationService
