import { createRoleHandlers } from 'components/pages/organisation-settings/tabs/trust-relationships/hooks/useTrustRelationshipRoles'
import { SelectedRole } from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipPermissionsFields'
import { TrustRelationship } from 'common/types/responses'

const trustRelationship = {
  audience: 'https://github.com/Flagsmith',
  claim_rules: [],
  created_at: '',
  created_by: null,
  id: 1,
  is_admin: false,
  issuer: 'https://token.actions.githubusercontent.com',
  master_api_key_id: 'key-id',
  master_api_key_prefix: 'prefix',
  name: 'GitHub Actions',
} as TrustRelationship

const role: SelectedRole = { id: 7, name: 'Deployer' }

type PendingRolesUpdate =
  | SelectedRole[]
  | ((previous: SelectedRole[]) => SelectedRole[])

const trackPendingRoles = () => {
  let state: SelectedRole[] = [role]
  const setPendingRoles = jest.fn((update: PendingRolesUpdate) => {
    state = typeof update === 'function' ? update(state) : update
  })
  return { getState: () => state, setPendingRoles }
}

// Lets the mutation promise chain settle before asserting.
const flushPromises = () => new Promise((resolve) => setTimeout(resolve, 0))

const mutations = () => ({
  assignRole: jest.fn().mockResolvedValue({}),
  detachRole: jest.fn().mockResolvedValue({}),
})

beforeEach(() => {
  ;(global as { toast?: unknown }).toast = jest.fn()
})

describe('addRole', () => {
  it('warns and leaves the selection alone when the API call fails', async () => {
    // Given
    const { assignRole, detachRole } = mutations()
    assignRole.mockRejectedValue({ status: 403 })
    const { getState, setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
      trustRelationship,
    })

    // When
    handlers.addRole({ id: 8, name: 'Reader' })
    await flushPromises()

    // Then
    expect(setPendingRoles).not.toHaveBeenCalled()
    expect(getState()).toEqual([role])
    expect(toast).toHaveBeenCalledWith('Could not assign role', 'danger')
  })

  it('assigns against the backing key in edit mode', async () => {
    // Given
    const { assignRole, detachRole } = mutations()
    const { setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
      trustRelationship,
    })

    // When
    handlers.addRole({ id: 8, name: 'Reader' })
    await flushPromises()

    // Then
    expect(assignRole).toHaveBeenCalledWith({
      body: { master_api_key: 'key-id' },
      org_id: 1,
      role_id: 8,
    })
    // The cache, not local state, carries the assigned roles in edit mode.
    expect(setPendingRoles).not.toHaveBeenCalled()
    expect(toast).toHaveBeenCalledWith('Role assigned')
  })

  it('holds the selection without an API call in create mode', () => {
    // Given
    const { assignRole, detachRole } = mutations()
    const { getState, setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
    })

    // When
    handlers.addRole({ id: 8, name: 'Reader' })

    // Then
    expect(assignRole).not.toHaveBeenCalled()
    expect(getState()).toEqual([role, { id: 8, name: 'Reader' }])
  })
})

describe('removeRole', () => {
  it('warns when the API call fails', async () => {
    // Given
    const { assignRole, detachRole } = mutations()
    detachRole.mockRejectedValue({ status: 403 })
    const { getState, setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
      trustRelationship,
    })

    // When
    handlers.removeRole(role.id)
    await flushPromises()

    // Then
    expect(setPendingRoles).not.toHaveBeenCalled()
    expect(getState()).toEqual([role])
    expect(toast).toHaveBeenCalledWith('Could not remove role', 'danger')
  })

  it('detaches from the backing key in edit mode', async () => {
    // Given
    const { assignRole, detachRole } = mutations()
    const { setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
      trustRelationship,
    })

    // When
    handlers.removeRole(role.id)
    await flushPromises()

    // Then
    expect(detachRole).toHaveBeenCalledWith({
      org_id: 1,
      prefix: 'prefix',
      role_id: role.id,
    })
    expect(setPendingRoles).not.toHaveBeenCalled()
    expect(toast).toHaveBeenCalledWith('Role removed')
  })

  it('drops the selection without an API call in create mode', () => {
    // Given
    const { assignRole, detachRole } = mutations()
    const { getState, setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
    })

    // When
    handlers.removeRole(role.id)

    // Then
    expect(detachRole).not.toHaveBeenCalled()
    expect(getState()).toEqual([])
  })
})

describe('assignRoles', () => {
  it('resolves false when any assignment fails', async () => {
    // Given
    const { assignRole, detachRole } = mutations()
    assignRole.mockResolvedValueOnce({}).mockRejectedValueOnce({ status: 404 })
    const { setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
    })

    // When
    const allAssigned = await handlers.assignRoles('key-id', [
      role,
      { id: 8, name: 'Reader' },
    ])

    // Then
    expect(allAssigned).toBe(false)
    expect(assignRole).toHaveBeenCalledTimes(2)
  })

  it('resolves true when every assignment succeeds', async () => {
    // Given
    const { assignRole, detachRole } = mutations()
    const { setPendingRoles } = trackPendingRoles()
    const handlers = createRoleHandlers({
      assignRole,
      detachRole,
      organisationId: 1,
      setPendingRoles,
    })

    // When
    const allAssigned = await handlers.assignRoles('key-id', [role])

    // Then
    expect(allAssigned).toBe(true)
    expect(assignRole).toHaveBeenCalledWith({
      body: { master_api_key: 'key-id' },
      org_id: 1,
      role_id: role.id,
    })
  })
})
