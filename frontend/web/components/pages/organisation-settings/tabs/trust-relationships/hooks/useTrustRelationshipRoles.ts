import { Dispatch, SetStateAction, useMemo, useState } from 'react'
import { Req } from 'common/types/requests'
import { TrustRelationship } from 'common/types/responses'
import { useCreateRoleMasterApiKeyMutation } from 'common/services/useRoleMasterApiKey'
import {
  useDeleteMasterAPIKeyWithMasterAPIKeyRolesMutation,
  useGetRolesMasterAPIKeyWithMasterAPIKeyRolesQuery,
} from 'common/services/useMasterAPIKeyWithMasterAPIKeyRole'
import { SelectedRole } from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipPermissionsFields'

type RoleHandlerContext = {
  organisationId: number
  trustRelationship?: TrustRelationship
  setPendingRoles: Dispatch<SetStateAction<SelectedRole[]>>
  // The mutation triggers, unwrapped: they reject when the API call fails.
  assignRole: (query: Req['createRoleMasterApiKey']) => Promise<unknown>
  detachRole: (
    query: Req['deleteMasterAPIKeyWithMasterAPIKeyRoles'],
  ) => Promise<unknown>
}

// The behaviour shared by both trust relationship forms.
// In edit mode, changes apply to the backing key immediately
// and the assigned roles come back from the RTK Query cache; in create mode,
// roles accumulate locally and are assigned after creation via `assignRoles`.
export const createRoleHandlers = ({
  assignRole,
  detachRole,
  organisationId,
  setPendingRoles,
  trustRelationship,
}: RoleHandlerContext) => ({
  addRole: (role: SelectedRole): void => {
    if (!trustRelationship) {
      // Roles are assigned after the trust relationship is created.
      setPendingRoles((selected) => [
        ...selected,
        { id: role.id, name: role.name },
      ])
      return
    }
    assignRole({
      body: { master_api_key: trustRelationship.master_api_key_id },
      org_id: organisationId,
      role_id: role.id,
    })
      .then(() => toast('Role assigned'))
      .catch(() => toast('Could not assign role', 'danger'))
  },
  assignRoles: async (
    masterApiKeyId: string,
    roles: SelectedRole[],
  ): Promise<boolean> => {
    // Create mode: assign the accumulated roles to the freshly created
    // relationship's backing key. Resolves whether every assignment
    // succeeded.
    const results = await Promise.all(
      roles.map((role) =>
        assignRole({
          body: { master_api_key: masterApiKeyId },
          org_id: organisationId,
          role_id: role.id,
        })
          .then(() => true)
          .catch(() => false),
      ),
    )
    return results.every(Boolean)
  },
  removeRole: (roleId: number): void => {
    if (!trustRelationship) {
      setPendingRoles((selected) =>
        selected.filter((role) => role.id !== roleId),
      )
      return
    }
    detachRole({
      org_id: organisationId,
      prefix: trustRelationship.master_api_key_prefix,
      role_id: roleId,
    })
      .then(() => toast('Role removed'))
      .catch(() => toast('Could not remove role', 'danger'))
  },
})

export default function useTrustRelationshipRoles(
  organisationId: number,
  trustRelationship?: TrustRelationship,
) {
  // Create mode has no backing key to assign to yet, so the selection is held
  // here until `assignRoles` runs. Edit mode reads it from the cache instead,
  // which both mutations invalidate — local state can't drift from the server.
  const [pendingRoles, setPendingRoles] = useState<SelectedRole[]>([])

  const { data } = useGetRolesMasterAPIKeyWithMasterAPIKeyRolesQuery(
    {
      org_id: organisationId,
      prefix: trustRelationship?.master_api_key_prefix || '',
    },
    { skip: !trustRelationship },
  )
  const [createRoleMasterApiKey] = useCreateRoleMasterApiKeyMutation()
  const [deleteMasterAPIKeyWithMasterAPIKeyRoles] =
    useDeleteMasterAPIKeyWithMasterAPIKeyRolesMutation()

  const handlers = useMemo(
    () =>
      createRoleHandlers({
        assignRole: (query) => createRoleMasterApiKey(query).unwrap(),
        detachRole: (query) =>
          deleteMasterAPIKeyWithMasterAPIKeyRoles(query).unwrap(),
        organisationId,
        setPendingRoles,
        trustRelationship,
      }),
    [
      createRoleMasterApiKey,
      deleteMasterAPIKeyWithMasterAPIKeyRoles,
      organisationId,
      trustRelationship,
    ],
  )

  const roles = useMemo(
    () => (trustRelationship ? data?.results || [] : pendingRoles),
    [data, pendingRoles, trustRelationship],
  )

  return {
    addRole: handlers.addRole,
    assignRoles: (masterApiKeyId: string) =>
      handlers.assignRoles(masterApiKeyId, pendingRoles),
    // Turning admin on detaches roles server-side when the relationship is
    // saved; only the not-yet-assigned selection is ours to drop.
    clearRoles: () => setPendingRoles([]),
    removeRole: handlers.removeRole,
    roles,
  }
}
