import { createRoleHandlers } from 'components/pages/organisation-settings/tabs/trust-relationships/hooks/useTrustRelationshipRoles'
import { SelectedRole } from 'components/pages/organisation-settings/tabs/trust-relationships/TrustRelationshipPermissionsFields'
import { TrustRelationship } from 'common/types/responses'
import { createRoleMasterApiKey } from 'common/services/useRoleMasterApiKey'
import { deleteMasterAPIKeyWithMasterAPIKeyRoles } from 'common/services/useMasterAPIKeyWithMasterAPIKeyRole'

jest.mock('common/store', () => ({ getStore: () => ({}) }))
jest.mock('common/services/useRoleMasterApiKey', () => ({
  createRoleMasterApiKey: jest.fn(),
}))
jest.mock('common/services/useMasterAPIKeyWithMasterAPIKeyRole', () => ({
  deleteMasterAPIKeyWithMasterAPIKeyRoles: jest.fn(),
  getRolesMasterAPIKeyWithMasterAPIKeyRoles: jest.fn(),
}))

const mockCreate = createRoleMasterApiKey as jest.Mock
const mockDelete = deleteMasterAPIKeyWithMasterAPIKeyRoles as jest.Mock

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

const trackRoles = () => {
  let state: SelectedRole[] = [role]
  const setRoles = jest.fn(
    (
      update: SelectedRole[] | ((previous: SelectedRole[]) => SelectedRole[]),
    ) => {
      state = typeof update === 'function' ? update(state) : update
    },
  )
  return { getState: () => state, setRoles }
}

beforeEach(() => {
  ;(global as { toast?: unknown }).toast = jest.fn()
})

describe('addRole', () => {
  it('does not update local state when the API call fails', async () => {
    // Given
    mockCreate.mockResolvedValue({ error: { status: 403 } })
    const { getState, setRoles } = trackRoles()
    const handlers = createRoleHandlers({
      organisationId: 1,
      setRoles,
      trustRelationship,
    })

    // When
    handlers.addRole({ id: 8, name: 'Reader' })
    await mockCreate.mock.results[0].value

    // Then
    expect(setRoles).not.toHaveBeenCalled()
    expect(getState()).toEqual([role])
    expect(toast).toHaveBeenCalledWith('Could not assign role', 'danger')
  })

  it('updates local state when the API call succeeds', async () => {
    // Given
    mockCreate.mockResolvedValue({ data: {} })
    const { getState, setRoles } = trackRoles()
    const handlers = createRoleHandlers({
      organisationId: 1,
      setRoles,
      trustRelationship,
    })

    // When
    handlers.addRole({ id: 8, name: 'Reader' })
    await mockCreate.mock.results[0].value

    // Then
    expect(getState()).toEqual([role, { id: 8, name: 'Reader' }])
    expect(toast).toHaveBeenCalledWith('Role assigned')
  })

  it('updates local state without an API call in create mode', () => {
    // Given
    const { getState, setRoles } = trackRoles()
    const handlers = createRoleHandlers({ organisationId: 1, setRoles })

    // When
    handlers.addRole({ id: 8, name: 'Reader' })

    // Then
    expect(mockCreate).not.toHaveBeenCalled()
    expect(getState()).toEqual([role, { id: 8, name: 'Reader' }])
  })
})

describe('removeRole', () => {
  it('does not update local state when the API call fails', async () => {
    // Given
    mockDelete.mockResolvedValue({ error: { status: 403 } })
    const { getState, setRoles } = trackRoles()
    const handlers = createRoleHandlers({
      organisationId: 1,
      setRoles,
      trustRelationship,
    })

    // When
    handlers.removeRole(role.id)
    await mockDelete.mock.results[0].value

    // Then
    expect(setRoles).not.toHaveBeenCalled()
    expect(getState()).toEqual([role])
    expect(toast).toHaveBeenCalledWith('Could not remove role', 'danger')
  })

  it('updates local state when the API call succeeds', async () => {
    // Given
    mockDelete.mockResolvedValue({ data: {} })
    const { getState, setRoles } = trackRoles()
    const handlers = createRoleHandlers({
      organisationId: 1,
      setRoles,
      trustRelationship,
    })

    // When
    handlers.removeRole(role.id)
    await mockDelete.mock.results[0].value

    // Then
    expect(getState()).toEqual([])
    expect(toast).toHaveBeenCalledWith('Role removed')
  })
})

describe('assignRoles', () => {
  it('resolves false when any assignment fails', async () => {
    // Given
    mockCreate
      .mockResolvedValueOnce({ data: {} })
      .mockResolvedValueOnce({ error: { status: 404 } })
    const { setRoles } = trackRoles()
    const handlers = createRoleHandlers({ organisationId: 1, setRoles })

    // When
    const allAssigned = await handlers.assignRoles('key-id', [
      role,
      { id: 8, name: 'Reader' },
    ])

    // Then
    expect(allAssigned).toBe(false)
    expect(mockCreate).toHaveBeenCalledTimes(2)
  })

  it('resolves true when every assignment succeeds', async () => {
    // Given
    mockCreate.mockResolvedValue({ data: {} })
    const { setRoles } = trackRoles()
    const handlers = createRoleHandlers({ organisationId: 1, setRoles })

    // When
    const allAssigned = await handlers.assignRoles('key-id', [role])

    // Then
    expect(allAssigned).toBe(true)
  })
})
