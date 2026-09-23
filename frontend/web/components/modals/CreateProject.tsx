import React, {
  FC,
  FormEvent,
  ReactElement,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import { RouteComponentProps } from 'react-router-dom'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import { setInterceptClose } from './base/ModalDefault'
import PlanBasedAccess from 'components/PlanBasedAccess'
import UserSelect from 'components/UserSelect'
import MyRoleSelect from 'components/MyRoleSelect'
import SettingsButton from 'components/SettingsButton'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import { useGetUsersQuery } from 'common/services/useUser'
import { useGetRolesQuery } from 'common/services/useRole'
import { useCreateProjectUserPermissionMutation } from 'common/services/useUserPermissions'
import { useCreateProjectRolePermissionMutation } from 'common/services/useRolePermission'
import AccountStore from 'common/stores/account-store'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import { Role, User } from 'common/types/responses'

type CreateProjectSavedData = {
  environmentId: number
  projectId: number
}

type CreateProjectProps = {
  history: RouteComponentProps['history']
  onSave?: (data: CreateProjectSavedData) => void
}

const CreateProject: FC<CreateProjectProps> = ({ history, onSave }) => {
  const [name, setName] = useState<string>('')
  const [adminIds, setAdminIds] = useState<number[]>([])
  const [adminRoleIds, setAdminRoleIds] = useState<number[]>([])
  const [showUsers, setShowUsers] = useState<boolean>(false)
  const [showRoles, setShowRoles] = useState<boolean>(false)
  const [assigningAdmins, setAssigningAdmins] = useState<boolean>(false)
  // InputGroup is a class component (untyped JS) exposing a `focus()` method.
  const inputRef = useRef<{ focus: () => void } | null>(null)
  // OrganisationProvider wires onSave into a Flux listener once on mount, so
  // any state we read in `close` is stale. Mirror selections into refs.
  const adminIdsRef = useRef<number[]>(adminIds)
  const adminRoleIdsRef = useRef<number[]>(adminRoleIds)
  adminIdsRef.current = adminIds
  adminRoleIdsRef.current = adminRoleIds
  const onSaveRef = useRef<CreateProjectProps['onSave']>(onSave)
  onSaveRef.current = onSave

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
  const [createUserPermission] = useCreateProjectUserPermissionMutation()
  const [createRolePermission] = useCreateProjectRolePermissionMutation()

  // Org administrators already have permissions on every project, and the
  // creator obviously has permissions on their own project — exclude both.
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

  useEffect(() => {
    const focusTimeout = setTimeout(() => {
      inputRef.current?.focus()
    }, 500)
    setInterceptClose(
      () =>
        new Promise<boolean>((resolve) => {
          history.push(document.location.pathname)
          setInterceptClose(null)
          resolve(true)
        }),
    )
    return () => clearTimeout(focusTimeout)
  }, [history])

  const assignProjectAdmins = async (projectId: number) => {
    const userIds = adminIdsRef.current
    const roleIds = adminRoleIdsRef.current
    const userRequests = userIds.map((userId) =>
      createUserPermission({
        body: { admin: true, permissions: [], user: userId },
        projectId,
      }).unwrap(),
    )
    const roleRequests = roleIds.map((roleId) =>
      createRolePermission({
        body: { admin: true, permissions: [], project: projectId },
        organisation_id: organisationId!,
        role_id: roleId,
      }).unwrap(),
    )
    const results = await Promise.allSettled([...userRequests, ...roleRequests])
    return results.filter((r) => r.status === 'rejected').length
  }

  const close = async (data?: CreateProjectSavedData | null) => {
    setInterceptClose(null)
    const { environmentId, projectId } = data || ({} as CreateProjectSavedData)
    const hasAssignments =
      adminIdsRef.current.length || adminRoleIdsRef.current.length
    if (projectId && hasAssignments) {
      setAssigningAdmins(true)
      const failures = await assignProjectAdmins(projectId)
      setAssigningAdmins(false)
      if (failures) {
        toast(
          `Project created — ${failures} admin assignment${
            failures > 1 ? 's' : ''
          } failed. Retry in Project Settings → Members.`,
          'danger',
        )
      }
    }
    closeModal()
    if (data) {
      history.push(
        `/project/${projectId}/environment/${environmentId}/features?new=true`,
      )
      onSaveRef.current?.(data)
    }
  }

  return (
    <OrganisationProvider onSave={close}>
      {({ createProject, error, isSaving, projects }) => {
        const hasProject = !!projects && !!projects.length
        const canCreate =
          !hasProject || !!Utils.getPlansPermission('CREATE_ADDITIONAL_PROJECT')
        const disableCreate = !canCreate
        const busy = isSaving || assigningAdmins
        const showUserSelector = !!eligibleAdmins.length
        const showRoleSelector = !!hasRbac && !!roles.length
        const showAdminSelector =
          (showUserSelector || showRoleSelector) && !disableCreate

        const inner: ReactElement = (
          <div className='p-4'>
            <form
              style={{ opacity: disableCreate ? 0.5 : 1 }}
              data-test='create-project-modal'
              id='create-project-modal'
              onSubmit={(e: FormEvent<HTMLFormElement>) => {
                if (disableCreate) {
                  return
                }
                e.preventDefault()
                const trimmedName = name.trim()
                if (!busy && trimmedName) {
                  createProject(trimmedName)
                }
              }}
            >
              <InputGroup
                ref={(e: { focus: () => void } | null) => {
                  inputRef.current = e
                }}
                data-test='projectName'
                disabled={disableCreate}
                className='mb-0'
                inputProps={{
                  className: 'full-width',
                  name: 'projectName',
                }}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setName(Utils.safeParseEventValue(e))
                }
                isValid={!!name.trim()}
                type='text'
                title='Project Name*'
                placeholder='My Product Name'
              />

              {showAdminSelector && (
                <div className='mt-4'>
                  <label className='form-label mb-1'>
                    Project administrators
                  </label>
                  <div className='text-muted text-small mb-3'>
                    Optionally grant other users or roles administrator access
                    to this project. Organisation administrators already have
                    full access to all projects.
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
                              setAdminIds(adminIds.filter((v) => v !== id))
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
                                    adminIds.filter((id) => id !== u.id),
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
                                    adminRoleIds.filter((id) => id !== r.id),
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
              )}

              {error && <ErrorMessage error={error} />}
              <div className='text-right mt-5'>
                <Button
                  type='submit'
                  data-test='create-project-btn'
                  id='create-project-btn'
                  disabled={!canCreate || busy || !name.trim()}
                  className='text-right'
                >
                  {busy ? 'Creating' : 'Create Project'}
                </Button>
              </div>
            </form>
          </div>
        )
        if (hasProject) {
          return (
            <>
              <PlanBasedAccess
                className='p-4'
                feature={'CREATE_ADDITIONAL_PROJECT'}
                theme={'page'}
              />
              {inner}
            </>
          )
        }
        return inner
      }}
    </OrganisationProvider>
  )
}

CreateProject.displayName = 'CreateProject'

export default CreateProject
