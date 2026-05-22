import React, { useEffect, useMemo, useRef, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import { setInterceptClose } from './base/ModalDefault'
import PlanBasedAccess from 'components/PlanBasedAccess'
import UserSelect from 'components/UserSelect'
import MyRoleSelect from 'components/MyRoleSelect'
import SettingsButton from 'components/SettingsButton'
import { useGetUsersQuery } from 'common/services/useUser'
import { useGetRolesQuery } from 'common/services/useRole'
import AccountStore from 'common/stores/account-store'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import _data from 'common/data/base/_data'
import ProjectApi from 'common/project'

const CreateProject = ({ history, onSave }) => {
  const [name, setName] = useState('')
  const [adminIds, setAdminIds] = useState([])
  const [adminRoleIds, setAdminRoleIds] = useState([])
  const [showUsers, setShowUsers] = useState(false)
  const [showRoles, setShowRoles] = useState(false)
  const [assigningAdmins, setAssigningAdmins] = useState(false)
  const inputRef = useRef(null)

  const organisationId = AccountStore.getOrganisation()?.id
  const currentUserId = AccountStore.getUser()?.id
  const hasRbac = Utils.getPlansPermission('RBAC')
  const { data: users } = useGetUsersQuery(
    { organisationId },
    { skip: !organisationId },
  )
  const { data: rolesData } = useGetRolesQuery(
    { organisation_id: organisationId },
    { skip: !organisationId || !hasRbac },
  )
  const roles = useMemo(() => rolesData?.results ?? [], [rolesData])

  // Org administrators already have permissions on every project, and the
  // creator obviously has permissions on their own project — exclude both.
  const eligibleAdmins = useMemo(
    () =>
      (users ?? []).filter((u) => u.role !== 'ADMIN' && u.id !== currentUserId),
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
        new Promise((resolve) => {
          history.push(document.location.pathname)
          setInterceptClose(null)
          resolve(true)
        }),
    )
    return () => clearTimeout(focusTimeout)
  }, [history])

  const assignProjectAdmins = (projectId) => {
    const userRequests = adminIds.map((userId) =>
      _data.post(`${ProjectApi.api}projects/${projectId}/user-permissions/`, {
        admin: true,
        permissions: [],
        user: userId,
      }),
    )
    const roleRequests = adminRoleIds.map((roleId) =>
      _data.post(
        `${ProjectApi.api}organisations/${organisationId}/roles/${roleId}/projects-permissions/`,
        {
          admin: true,
          permissions: [],
          project: projectId,
        },
      ),
    )
    return Promise.all([...userRequests, ...roleRequests])
  }

  const close = async (data = {}) => {
    setInterceptClose(null)
    const { environmentId, projectId } = data
    const hasAssignments = adminIds.length || adminRoleIds.length
    if (projectId && hasAssignments) {
      setAssigningAdmins(true)
      try {
        await assignProjectAdmins(projectId)
      } catch (e) {
        toast('Failed to assign one or more project administrators', 'danger')
      } finally {
        setAssigningAdmins(false)
      }
    }
    closeModal()
    if (data) {
      history.push(
        `/project/${projectId}/environment/${environmentId}/features?new=true`,
      )
      onSave?.(data)
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
        const showRoleSelector = hasRbac && !!roles.length
        const showAdminSelector = showUserSelector || showRoleSelector

        const inner = (
          <div className='p-4'>
            <form
              style={{ opacity: disableCreate ? 0.5 : 1 }}
              data-test='create-project-modal'
              id='create-project-modal'
              onSubmit={(e) => {
                if (disableCreate) {
                  return
                }
                e.preventDefault()
                !busy && name && createProject(name)
              }}
            >
              <InputGroup
                ref={(e) => (inputRef.current = e)}
                data-test='projectName'
                disabled={disableCreate}
                className='mb-0'
                inputProps={{
                  className: 'full-width',
                  name: 'projectName',
                }}
                onChange={(e) => setName(Utils.safeParseEventValue(e))}
                isValid={name && name.length}
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
                    Optionally grant other users, groups, or roles administrator
                    access to this project. Organisation administrators already
                    have full access to all projects.
                  </div>
                  {showUserSelector && (
                    <div className='mb-3'>
                      <SettingsButton
                        onClick={() =>
                          !disableCreate && setShowUsers(!showUsers)
                        }
                        dropdown={
                          <UserSelect
                            users={eligibleAdmins}
                            value={adminIds}
                            onAdd={(id) => setAdminIds([...adminIds, id])}
                            onRemove={(id) =>
                              setAdminIds(adminIds.filter((v) => v !== id))
                            }
                            isOpen={showUsers}
                            onToggle={() => setShowUsers(!showUsers)}
                          />
                        }
                        content={
                          <Row style={{ rowGap: '12px' }}>
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
                        onClick={() =>
                          !disableCreate && setShowRoles(!showRoles)
                        }
                        dropdown={
                          <MyRoleSelect
                            orgId={organisationId}
                            value={adminRoleIds}
                            onAdd={(id) =>
                              setAdminRoleIds([...adminRoleIds, id])
                            }
                            onRemove={(id) =>
                              setAdminRoleIds(
                                adminRoleIds.filter((v) => v !== id),
                              )
                            }
                            isOpen={showRoles}
                            onToggle={() => setShowRoles(!showRoles)}
                          />
                        }
                        content={
                          <Row style={{ rowGap: '12px' }}>
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
                  disabled={!canCreate || busy || !name}
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
