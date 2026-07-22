import { Dispatch, SetStateAction, useEffect, useMemo, useState } from 'react'
import { getStore } from 'common/store'
import { TrustRelationship } from 'common/types/responses'
import { createRoleMasterApiKey } from 'common/services/useRoleMasterApiKey'
import {
  deleteMasterAPIKeyWithMasterAPIKeyRoles,
  getRolesMasterAPIKeyWithMasterAPIKeyRoles,
} from 'common/services/useMasterAPIKeyWithMasterAPIKeyRole'
import { SelectedRole } from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipPermissionsFields'

type RoleHandlerContext = {
  organisationId: number
  trustRelationship?: TrustRelationship
  setRoles: Dispatch<SetStateAction<SelectedRole[]>>
}

// The behaviour shared by both trust relationship forms, kept free of React
// so it can be unit tested. In edit mode, changes apply to the backing key
// immediately and local state only follows confirmed API results; in create
// mode, roles accumulate locally and are assigned after creation via
// `assignRoles`.
export const createRoleHandlers = ({
  organisationId,
  setRoles,
  trustRelationship,
}: RoleHandlerContext) => ({
  addRole: (role: SelectedRole): void => {
    if (!trustRelationship) {
      // Roles are assigned after the trust relationship is created.
      setRoles((selected) => [...selected, { id: role.id, name: role.name }])
      return
    }
    createRoleMasterApiKey(getStore(), {
      body: { master_api_key: trustRelationship.master_api_key_id },
      org_id: organisationId,
      role_id: role.id,
    }).then((res: { error?: unknown }) => {
      if (res.error) {
        toast('Could not assign role', 'danger')
        return
      }
      setRoles((selected) => [...selected, { id: role.id, name: role.name }])
      toast('Role assigned')
    })
  },
  assignRoles: async (
    masterApiKeyId: string,
    roles: SelectedRole[],
  ): Promise<boolean> => {
    // Create mode: assign the accumulated roles to the freshly created
    // relationship's backing key. Resolves whether every assignment
    // succeeded.
    const results: { error?: unknown }[] = await Promise.all(
      roles.map((role) =>
        createRoleMasterApiKey(getStore(), {
          body: { master_api_key: masterApiKeyId },
          org_id: organisationId,
          role_id: role.id,
        }),
      ),
    )
    return results.every((res) => !res.error)
  },
  removeRole: (roleId: number): void => {
    if (!trustRelationship) {
      setRoles((selected) => selected.filter((role) => role.id !== roleId))
      return
    }
    deleteMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
      org_id: organisationId,
      prefix: trustRelationship.master_api_key_prefix,
      role_id: roleId,
    }).then((res: { error?: unknown }) => {
      if (res.error) {
        toast('Could not remove role', 'danger')
        return
      }
      setRoles((selected) => selected.filter((role) => role.id !== roleId))
      toast('Role removed')
    })
  },
})

export default function useTrustRelationshipRoles(
  organisationId: number,
  trustRelationship?: TrustRelationship,
) {
  const [roles, setRoles] = useState<SelectedRole[]>([])

  useEffect(() => {
    if (trustRelationship) {
      getRolesMasterAPIKeyWithMasterAPIKeyRoles(getStore(), {
        org_id: organisationId,
        prefix: trustRelationship.master_api_key_prefix,
      }).then((res: { data?: { results: SelectedRole[] } }) => {
        setRoles(res.data?.results || [])
      })
    }
  }, [organisationId, trustRelationship])

  const handlers = useMemo(
    () => createRoleHandlers({ organisationId, setRoles, trustRelationship }),
    [organisationId, trustRelationship],
  )

  return {
    addRole: handlers.addRole,
    assignRoles: (masterApiKeyId: string) =>
      handlers.assignRoles(masterApiKeyId, roles),
    // Turning admin on detaches roles server-side; mirror that locally.
    clearRoles: () => setRoles([]),
    removeRole: handlers.removeRole,
    roles,
  }
}
