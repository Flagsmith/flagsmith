import React, { useEffect, useMemo, useRef, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'
import PageTitle from 'components/PageTitle'
import CondensedRow from 'components/CondensedRow'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import { getStore } from 'common/store'
import ProjectProvider, {
  CreateEnvType,
} from 'common/providers/ProjectProvider'
import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import { useHistory } from 'react-router-dom'
import API from 'project/api'
import InputGroup from 'components/base/forms/InputGroup'
import { Environment, Role, User } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import UserSelect from 'components/UserSelect'
import MyRoleSelect from 'components/MyRoleSelect'
import SettingsButton from 'components/SettingsButton'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import { useGetUsersQuery } from 'common/services/useUser'
import { useGetRolesQuery } from 'common/services/useRole'
import { useCreateEnvironmentUserPermissionMutation } from 'common/services/useUserPermissions'
import { useCreateEnvironmentRolePermissionMutation } from 'common/services/useRolePermission'
import { useRouteContext } from 'components/providers/RouteContext'
import { ProjectPermission } from 'common/types/permissions.types'

const CreateEnvironmentPage: React.FC = () => {
  const [envContentType, setEnvContentType] = useState<Record<string, any>>({})
  const [metadata, setMetadata] = useState<any[]>([])
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string | undefined>()
  const [selectedEnv, setSelectedEnv] = useState<any | undefined>()
  const [hasMetadataRequired, setHasMetadataRequired] = useState(false)
  const [adminIds, setAdminIds] = useState<number[]>([])
  const [adminRoleIds, setAdminRoleIds] = useState<number[]>([])
  const [showUsers, setShowUsers] = useState<boolean>(false)
  const [showRoles, setShowRoles] = useState<boolean>(false)
  const [assigningAdmins, setAssigningAdmins] = useState<boolean>(false)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const history = useHistory()
  const { projectId } = useRouteContext()

  // ProjectProvider wires onSave into a Flux listener once on mount, so any
  // state we read in the saved handler is stale. Mirror selections into refs.
  const adminIdsRef = useRef<number[]>(adminIds)
  const adminRoleIdsRef = useRef<number[]>(adminRoleIds)
  const projectIdRef = useRef<number | undefined>(projectId)
  adminIdsRef.current = adminIds
  adminRoleIdsRef.current = adminRoleIds
  projectIdRef.current = projectId

  const organisationId = AccountStore.getOrganisation()?.id as
    | number
    | undefined
  const currentUserId = AccountStore.getUser()?.id as number | undefined
  const hasRbac = Utils.getPlansPermission('RBAC')
  const { data: users } = useGetUsersQuery(
    { organisationId: organisationId! },
    { skip: !organisationId },
  )
  const { data: rolesData } = useGetRolesQuery(
    { organisation_id: organisationId! },
    { skip: !organisationId || !hasRbac },
  )
  const roles = useMemo<Role[]>(() => rolesData?.results ?? [], [rolesData])
  const [createUserPermission] = useCreateEnvironmentUserPermissionMutation()
  const [createRolePermission] = useCreateEnvironmentRolePermissionMutation()

  // Org administrators already have permissions on every environment, and the
  // creator obviously has permissions on their own environment — exclude both.
  const eligibleAdmins = useMemo<User[]>(
    () =>
      (users ?? []).filter(
        (u: User) => u.role !== 'ADMIN' && u.id !== currentUserId,
      ),
    [users, currentUserId],
  )

  const selectedAdmins = useMemo(
    () => eligibleAdmins.filter((u) => adminIds.includes(u.id)),
    [eligibleAdmins, adminIds],
  )
  const selectedRoles = useMemo(
    () => roles.filter((r) => adminRoleIds.includes(r.id)),
    [roles, adminRoleIds],
  )

  const assignEnvironmentAdmins = async (environment: Environment) => {
    const userIds = adminIdsRef.current
    const roleIds = adminRoleIdsRef.current
    const orgId = AccountStore.getOrganisation()?.id
    const userRequests = userIds.map((userId) =>
      createUserPermission({
        body: { admin: true, permissions: [], user: userId },
        environmentId: environment.api_key,
      }).unwrap(),
    )
    const roleRequests = roleIds.map((roleId) =>
      createRolePermission({
        body: { admin: true, environment: environment.id, permissions: [] },
        organisation_id: orgId!,
        role_id: roleId,
      }).unwrap(),
    )
    const results = await Promise.allSettled([...userRequests, ...roleRequests])
    return results.filter((r) => r.status === 'rejected').length
  }

  const onSave = async (environment: Environment) => {
    const hasAssignments =
      adminIdsRef.current.length || adminRoleIdsRef.current.length
    if (hasAssignments) {
      setAssigningAdmins(true)
      const failures = await assignEnvironmentAdmins(environment)
      setAssigningAdmins(false)
      if (failures) {
        toast(
          `Environment created — ${failures} admin assignment${
            failures > 1 ? 's' : ''
          } failed. Retry in Environment Settings → Permissions.`,
          'danger',
        )
      }
    }
    history.push(
      `/project/${projectIdRef.current}/environment/${environment.api_key}/features`,
    )
  }

  useEffect(() => {
    API.trackPage(Constants.pages.CREATE_ENVIRONMENT)

    if (Utils.getPlansPermission('METADATA')) {
      getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        const contentType = Utils.getContentType(
          res.data,
          'model',
          'environment',
        )
        setEnvContentType(contentType)
      })
    }

    const focusTimeout = setTimeout(() => {
      if (!E2E) {
        inputRef.current?.focus()
      }
    }, 500)

    return () => clearTimeout(focusTimeout)
  }, [])

  const handleCreateEnv =
    (createEnv: CreateEnvType, busy: boolean) => (e: React.FormEvent) => {
      e.preventDefault()
      if (name && !busy && projectId) {
        createEnv({
          cloneFeatureStatesAsync: true,
          cloneId: selectedEnv?.api_key,
          description,
          metadata,
          name,
          projectId,
        })
      }
    }

  return (
    <div className='app-container container'>
      <PageTitle title='Create Environment'>
        {Constants.strings.ENVIRONMENT_DESCRIPTION}
      </PageTitle>
      <Permission
        level='project'
        permission={ProjectPermission.CREATE_ENVIRONMENT}
        id={projectId}
      >
        {({ isLoading, permission }) => {
          if (isLoading) {
            return <Loader />
          }
          if (!permission) {
            return (
              <div>
                <p className='notification__text'>
                  Check your project permissions
                </p>
                <p>
                  Although you have been invited to this project, you are not
                  invited to any environments yet!
                </p>
                <p>
                  Contact your project administrator asking them to either:
                  <ul>
                    <li>
                      Invite you to an environment (e.g. develop) by visiting{' '}
                      <strong>Environment settings</strong>
                    </li>
                    <li>
                      Grant permissions to create an environment under{' '}
                      <strong>Project settings</strong>.
                    </li>
                  </ul>
                </p>
              </div>
            )
          }
          const showUserSelector = !!eligibleAdmins.length
          const showRoleSelector = !!hasRbac && !!roles.length
          const showAdminSelector = showUserSelector || showRoleSelector
          return (
            <ProjectProvider id={projectId} onSave={onSave}>
              {({ createEnv, error, isSaving, project }) => {
                const busy = isSaving || assigningAdmins
                return (
                  <form
                    id='create-env-modal'
                    onSubmit={handleCreateEnv(createEnv, busy)}
                  >
                    <div className='mt-5'>
                      <CondensedRow>
                        <InputGroup
                          ref={inputRef as any}
                          inputProps={{
                            className: 'full-width',
                            name: 'envName',
                          }}
                          onChange={(e: InputEvent) =>
                            setName(Utils.safeParseEventValue(e))
                          }
                          isValid={!!name}
                          type='text'
                          title='Name*'
                          placeholder='An environment name e.g. Develop'
                        />
                      </CondensedRow>
                      <CondensedRow>
                        <InputGroup
                          textarea
                          ref={inputRef as any}
                          value={description}
                          inputProps={{ className: 'input--wide textarea-lg' }}
                          onChange={(e: InputEvent) =>
                            setDescription(Utils.safeParseEventValue(e))
                          }
                          isValid={!!name}
                          type='text'
                          title='Description'
                          placeholder='Environment Description'
                        />
                      </CondensedRow>
                      <CondensedRow>
                        {!!project?.environments?.length && (
                          <InputGroup
                            tooltip='This will copy feature enabled states and remote config values from the selected environment.'
                            title='Clone from environment'
                            component={
                              <Select
                                onChange={(env: { value: string }) => {
                                  setSelectedEnv(
                                    project?.environments.find(
                                      (v) => v.api_key === env.value,
                                    ),
                                  )
                                }}
                                options={project.environments.map((env) => ({
                                  label: env.name,
                                  value: env.api_key,
                                }))}
                                value={
                                  selectedEnv
                                    ? {
                                        label: selectedEnv.name,
                                        value: selectedEnv.api_key,
                                      }
                                    : { label: 'Please select an environment' }
                                }
                              />
                            }
                          />
                        )}
                      </CondensedRow>
                      {showAdminSelector && (
                        <CondensedRow>
                          <div>
                            <label className='form-label mb-1'>
                              Environment administrators
                            </label>
                            <div className='text-muted text-small mb-3'>
                              Optionally grant other users or roles
                              administrator access to this environment.
                              Organisation administrators already have full
                              access to all environments.
                            </div>
                            {showUserSelector && (
                              <div className='mb-3'>
                                <SettingsButton
                                  onClick={() => setShowUsers(!showUsers)}
                                  dropdown={
                                    <UserSelect
                                      users={eligibleAdmins}
                                      value={adminIds}
                                      onAdd={(id: number) =>
                                        setAdminIds([...adminIds, id])
                                      }
                                      onRemove={(id: number) =>
                                        setAdminIds(
                                          adminIds.filter((v) => v !== id),
                                        )
                                      }
                                      isOpen={showUsers}
                                      onToggle={() => setShowUsers(!showUsers)}
                                    />
                                  }
                                  content={
                                    <Row className='row-gap-3'>
                                      {selectedAdmins.map((u) => (
                                        <Row
                                          key={u.id}
                                          onClick={() =>
                                            setAdminIds(
                                              adminIds.filter(
                                                (id) => id !== u.id,
                                              ),
                                            )
                                          }
                                          className='chip mr-2'
                                        >
                                          <span>{getUserDisplayName(u)}</span>
                                          <span className='chip-icon ion'>
                                            <IonIcon icon={closeIcon} />
                                          </span>
                                        </Row>
                                      ))}
                                      {!selectedAdmins.length && (
                                        <div className='text-muted'>
                                          No users assigned
                                        </div>
                                      )}
                                    </Row>
                                  }
                                >
                                  Users
                                </SettingsButton>
                              </div>
                            )}
                            {showRoleSelector && (
                              <div className='mb-3'>
                                <SettingsButton
                                  onClick={() => setShowRoles(!showRoles)}
                                  dropdown={
                                    <MyRoleSelect
                                      orgId={organisationId!}
                                      value={adminRoleIds}
                                      onAdd={(id: number) =>
                                        setAdminRoleIds([...adminRoleIds, id])
                                      }
                                      onRemove={(id: number) =>
                                        setAdminRoleIds(
                                          adminRoleIds.filter((v) => v !== id),
                                        )
                                      }
                                      isOpen={showRoles}
                                      onToggle={() => setShowRoles(!showRoles)}
                                    />
                                  }
                                  content={
                                    <Row className='row-gap-3'>
                                      {selectedRoles.map((r) => (
                                        <Row
                                          key={r.id}
                                          onClick={() =>
                                            setAdminRoleIds(
                                              adminRoleIds.filter(
                                                (id) => id !== r.id,
                                              ),
                                            )
                                          }
                                          className='chip mr-2'
                                        >
                                          <span>{r.name}</span>
                                          <span className='chip-icon ion'>
                                            <IonIcon icon={closeIcon} />
                                          </span>
                                        </Row>
                                      ))}
                                      {!selectedRoles.length && (
                                        <div className='text-muted'>
                                          No roles assigned
                                        </div>
                                      )}
                                    </Row>
                                  }
                                >
                                  Roles
                                </SettingsButton>
                              </div>
                            )}
                          </div>
                        </CondensedRow>
                      )}
                    </div>
                    {Utils.getPlansPermission('METADATA') &&
                      envContentType?.id && (
                        <CondensedRow>
                          <FormGroup className='mt-2 setting'>
                            <InputGroup
                              title='Custom fields'
                              tooltip='You need to add a value to the custom field if it is required to successfully clone the environment'
                              tooltipPlace='right'
                              component={
                                <AddMetadataToEntity
                                  organisationId={
                                    AccountStore.getOrganisation().id
                                  }
                                  projectId={projectId}
                                  entityId={selectedEnv?.api_key}
                                  envName={name}
                                  entityContentType={envContentType.id}
                                  entity={envContentType.model}
                                  isCloningEnvironment
                                  onChange={setMetadata}
                                  setHasMetadataRequired={
                                    setHasMetadataRequired
                                  }
                                />
                              }
                            />
                          </FormGroup>
                        </CondensedRow>
                      )}
                    {error && (
                      <CondensedRow>
                        <ErrorMessage error={error} />
                      </CondensedRow>
                    )}
                    <CondensedRow>
                      <div className='text-right'>
                        <Button
                          id='create-env-btn'
                          className='mt-3'
                          type='submit'
                          disabled={busy || !name || hasMetadataRequired}
                        >
                          {busy ? 'Creating' : 'Create Environment'}
                        </Button>
                      </div>
                    </CondensedRow>
                    <hr />
                    <p className='faint mt-2'>
                      Not seeing an environment? Check that your project
                      administrator has invited you to it.
                    </p>
                  </form>
                )
              }}
            </ProjectProvider>
          )
        }}
      </Permission>
    </div>
  )
}

export default ConfigProvider(CreateEnvironmentPage)
