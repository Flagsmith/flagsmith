import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

const integrationListUrl = ({
  environmentId,
  integrationId,
  organisationId,
  projectId,
}: {
  integrationId: string
  environmentId?: string
  projectId?: string
  organisationId?: string
}) => {
  if (organisationId) {
    return `organisations/${organisationId}/integrations/${integrationId}/`
  }
  if (environmentId) {
    return `environments/${environmentId}/integrations/${integrationId}/`
  }
  return `projects/${projectId}/integrations/${integrationId}/`
}

const integrationTag = ({
  environmentId,
  integrationId,
  organisationId,
  projectId,
}: {
  integrationId: string
  environmentId?: string
  projectId?: string
  organisationId?: string
}) => ({
  id: `${integrationId}:${organisationId ?? ''}:${projectId ?? ''}:${
    environmentId ?? ''
  }`,
  type: 'Integration' as const,
})

export const integrationService = service
  .enhanceEndpoints({ addTagTypes: ['Integration'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createIntegration: builder.mutation<
        Res['integration'][number],
        Req['createIntegration']
      >({
        invalidatesTags: (_res, err, args) =>
          err ? [] : [integrationTag(args)],
        query: ({ body, ...args }) => ({
          body,
          method: 'POST',
          url: integrationListUrl(args),
        }),
      }),
      getIntegration: builder.query<Res['integration'], Req['getIntegration']>({
        providesTags: (_res, _err, args) => [integrationTag(args)],
        query: (args) => ({ url: integrationListUrl(args) }),
      }),
      updateIntegration: builder.mutation<
        Res['integration'][number],
        Req['updateIntegration']
      >({
        invalidatesTags: (_res, err, args) =>
          err ? [] : [integrationTag(args)],
        query: ({ body, id, ...args }) => ({
          body,
          method: 'PUT',
          url: `${integrationListUrl(args)}${id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useCreateIntegrationMutation,
  useGetIntegrationQuery,
  useUpdateIntegrationMutation,
  // END OF EXPORTS
} = integrationService
