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

export const {
  useCreateUserInviteMutation,
  useDeleteUserInviteMutation,
  useGetUserInvitesQuery,
  useResendUserInviteMutation,
} = invitesService

/* Usage examples:
const { data, isLoading } = useGetRolesQuery({ id: 2 }, {}) //get hook
const [createRole, { isLoading, data, isSuccess }] = useCreateRoleMutation() //create hook
roleService.endpoints.getRoles.select({id: 2})(store.getState()) //access data from any function
*/
