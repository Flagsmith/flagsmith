import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userPermissionsService = service
  .enhanceEndpoints({ addTagTypes: ['UserPermissions'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getUserPermissions: builder.query<
        Res['userPermissions'],
        Req['getUserPermissions']
      >({
        providesTags: [{ id: 'LIST', type: 'UserPermissions' }],
        // TODO: Uncomment this once the API is implemented
        // query: (query: Req['getUserPermissions']) => ({
        //   url: `${query.level}s/${query.projectId}/user-permissions/${query.userId}/`,
        // }),
        // TODO: Remove this once the API is implemented
        queryFn: async ({ id, level, userId }) => {
          if (level === 'project') {
            return {
              data: {
                admin: false,
                permissions: [
                  {
                    derived_from: {
                      groups: [
                        {
                          'external_id': null,
                          'id': 617,
                          'is_default': false,
                          'name': 'group1',
                          'users': [],
                        },
                        {
                          'external_id': null,
                          'id': 618,
                          'is_default': false,
                          'name': 'group2',
                          'users': [],
                        },
                        {
                          'external_id': null,
                          'id': 619,
                          'is_default': false,
                          'name': 'group3',
                          'users': [],
                        },
                      ],
                      roles: [
                        {
                          'description': 'role_1',
                          'id': 227,
                          'name': 'role1',
                          'organisation': 5692,
                          tags: [],
                        },
                      ],
                    },
                    is_directly_granted: false,
                    permission_key: 'VIEW_PROJECT',
                    tags: [],
                  },
                ],
              },
            }
          }

          if (level === 'organisation') {
            return {
              data: {
                admin: false,
                permissions: [
                  {
                    derived_from: undefined,
                    is_directly_granted: true,
                    permission_key: 'MANAGE_USERS',
                    tags: [],
                  },
                ],
              },
            }
          }

          if (level === 'environment') {
            return {
              data: {
                admin: false,
                permissions: [
                  {
                    derived_from: {
                      groups: [
                        {
                          'external_id': null,
                          'id': 617,
                          'is_default': false,
                          'name': 'group1',
                          'users': [],
                        },
                        {
                          'external_id': null,
                          'id': 618,
                          'is_default': false,
                          'name': 'group2',
                          'users': [],
                        },
                      ],
                      roles: [
                        {
                          'description': 'role_1',
                          'id': 227,
                          'name': 'role1',
                          'organisation': 5692,
                          tags: [],
                        },
                      ],
                    },
                    is_directly_granted: false,
                    permission_key: 'VIEW_ENVIRONMENT',
                    tags: [],
                  },
                  {
                    derived_from: {
                      roles: [
                        {
                          'description': 'role_1',
                          'id': 227,
                          'name': 'role1',
                          'organisation': 5692,
                          tags: [],
                        },
                      ],
                    },
                    is_directly_granted: false,
                    permission_key: 'MANAGE_IDENTITIES',
                    tags: [],
                  },
                  {
                    derived_from: undefined,
                    is_directly_granted: true,
                    permission_key: 'CREATE_CHANGE_REQUEST',
                    tags: [],
                  },
                ],
              },
            }
          }

          return {
            data: {},
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getUserPermissions(
  store: any,
  data: Req['getUserPermissions'],
  options?: Parameters<
    typeof userPermissionsService.endpoints.getUserPermissions.initiate
  >[1],
) {
  return store.dispatch(
    userPermissionsService.endpoints.getUserPermissions.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetUserPermissionsQuery,
  // END OF EXPORTS
} = userPermissionsService

/* Usage examples:
const { data, isLoading } = useGetUserEnvironmentPermissionsQuery({ environmentId: aA1x3Ysd, userId: 1 }, {}) //get hook
userPermissionsService.endpoints.getUserEnvironmentPermissions.select({ environmentId: aA1x3Ysd, userId: 1 })(store.getState()) //access data from any function
*/
