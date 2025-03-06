import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Constants from 'common/constants'
import API from 'project/api'

export const invitesService = service
  .enhanceEndpoints({ addTagTypes: ['Invite'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createUserInvite: builder.mutation<
        Res['userInvite'],
        Req['createUserInvite']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Invite' }],
        query: (query: Req['createUserInvite']) => ({
          body: {
            frontend_base_url: `${document.location.origin}/email-invite/`,
            invites: query.invites.map((invite) => {
              API.trackEvent(Constants.events.INVITE)
              return invite
            }),
          },
          method: 'POST',
          url: `organisations/${query.organisationId}/invite/`,
        }),
      }),
      deleteUserInvite: builder.mutation<{}, Req['deleteUserInvite']>({
        invalidatesTags: [{ id: 'LIST', type: 'Invite' }],
        query: (query: Req['deleteUserInvite']) => {
          API.trackEvent(Constants.events.DELETE_INVITE)
          return {
            method: 'DELETE',
            url: `organisations/${query.organisationId}/invites/${query.inviteId}/`,
          }
        },
      }),
      getUserInvites: builder.query<Res['userInvites'], Req['getUserInvites']>({
        providesTags: [{ id: 'LIST', type: 'Invite' }],
        query: (query: Req['getUserInvites']) => ({
          url: `organisations/${query.organisationId}/invites/`,
        }),
      }),
      resendUserInvite: builder.mutation<{}, Req['resendUserInvite']>({
        invalidatesTags: [{ id: 'LIST', type: 'Invite' }],
        query: (query: Req['resendUserInvite']) => {
          API.trackEvent(Constants.events.RESEND_INVITE)
          return {
            method: 'POST',
            url: `organisations/${query.organisationId}/invites/${query.inviteId}/resend/`,
          }
        },
      }),
    }),
  })

export async function createUserInvite(
  store: any,
  data: Req['createUserInvite'],
  options?: Parameters<
    typeof invitesService.endpoints.createUserInvite.initiate
  >[1],
) {
  return store.dispatch(
    invitesService.endpoints.createUserInvite.initiate(data, options),
  )
}

export async function deleteUserInvite(
  store: any,
  data: Req['deleteUserInvite'],
  options?: Parameters<
    typeof invitesService.endpoints.deleteUserInvite.initiate
  >[1],
) {
  return store.dispatch(
    invitesService.endpoints.deleteUserInvite.initiate(data, options),
  )
}

export async function getUserInvites(
  store: any,
  data: Req['getUserInvites'],
  options?: Parameters<
    typeof invitesService.endpoints.getUserInvites.initiate
  >[1],
) {
  return store.dispatch(
    invitesService.endpoints.getUserInvites.initiate(data, options),
  )
}

export async function resendUserInvite(
  store: any,
  data: Req['resendUserInvite'],
  options?: Parameters<
    typeof invitesService.endpoints.resendUserInvite.initiate
  >[1],
) {
  return store.dispatch(
    invitesService.endpoints.resendUserInvite.initiate(data, options),
  )
}

export const {
  useCreateUserInviteMutation,
  useDeleteUserInviteMutation,
  useGetUserInvitesQuery,
  useResendUserInviteMutation,
} = invitesService
