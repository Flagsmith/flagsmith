import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const organisationUsageNotificationService = service
  .enhanceEndpoints({ addTagTypes: ['OrganisationUsageNotification'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getOrganisationUsageNotifications: builder.query<
        Res['organisationUsageNotifications'],
        Req['getOrganisationUsageNotifications']
      >({
        providesTags: [{ id: 'LIST', type: 'OrganisationUsageNotification' }],
        query: (query: Req['getOrganisationUsageNotifications']) => ({
          url: `organisations/${query.organisationId}/api-usage-notification/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useGetOrganisationUsageNotificationsQuery,
  // END OF EXPORTS
} = organisationUsageNotificationService
