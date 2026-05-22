import React, { useEffect, useMemo, useRef, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import { setInterceptClose } from './base/ModalDefault'
import PlanBasedAccess from 'components/PlanBasedAccess'
import InlineModal from 'components/InlineModal'
import Input from 'components/base/forms/Input'
import Icon from 'components/icons/Icon'
import classNames from 'classnames'
import SettingsButton from 'components/SettingsButton'
import { useGetUsersQuery } from 'common/services/useUser'
import { useGetGroupsQuery } from 'common/services/useGroup'
import { useGetRolesQuery } from 'common/services/useRole'
import AccountStore from 'common/stores/account-store'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import _data from 'common/data/base/_data'
import ProjectApi from 'common/project'

const CreateProject = ({ history, onSave }) => {
  const [name, setName] = useState('')
  const [adminIds, setAdminIds] = useState([])
  const [adminGroupIds, setAdminGroupIds] = useState([])
  const [adminRoleIds, setAdminRoleIds] = useState([])
  const [showPicker, setShowPicker] = useState(false)
  const [pickerFilter, setPickerFilter] = useState('')
  const [assigningAdmins, setAssigningAdmins] = useState(false)
  const inputRef = useRef(null)
  const pickerSearchRef = useRef(null)

  const organisationId = AccountStore.getOrganisation()?.id
  const currentUserId = AccountStore.getUser()?.id
  const hasRbac = Utils.getPlansPermission('RBAC')
  const { data: users } = useGetUsersQuery(
    { organisationId },
    { skip: !organisationId },
  )
  const { data: groupsData } = useGetGroupsQuery(
    { orgId: organisationId, page: 1 },
    { skip: !organisationId },
  )
  const { data: rolesData } = useGetRolesQuery(
    { organisation_id: organisationId },
    { skip: !organisationId || !hasRbac },
  )
  const groups = useMemo(() => groupsData?.results ?? [], [groupsData])
  const roles = useMemo(() => rolesData?.results ?? [], [rolesData])

  // Org administrators already have permissions on every project, and the
  // creator obviously has permissions on their own project — exclude both.
  const eligibleAdmins = useMemo(
    () =>
      (users ?? []).filter((u) => u.role !== 'ADMIN' && u.id !== currentUserId),
    [users, currentUserId],
  )

  const pickerItems = useMemo(() => {
    const userItems = eligibleAdmins.map((u) => ({
      id: u.id,
      label: getUserDisplayName(u),
      sublabel: u.email,
      type: 'user',
      typeLabel: 'User',
    }))
    const groupItems = groups.map((g) => ({
      id: g.id,
      label: g.name,
      sublabel: 'Group',
      type: 'group',
      typeLabel: 'Group',
    }))
    const roleItems = hasRbac
      ? roles.map((r) => ({
          id: r.id,
          label: r.name,
          sublabel: 'Role',
          type: 'role',
          typeLabel: 'Role',
        }))
      : []
    return [...userItems, ...groupItems, ...roleItems]
  }, [eligibleAdmins, groups, roles, hasRbac])

  const isSelected = (item) => {
    if (item.type === 'user') return adminIds.includes(item.id)
    if (item.type === 'group') return adminGroupIds.includes(item.id)
    return adminRoleIds.includes(item.id)
  }

  const toggleItem = (item) => {
    if (item.type === 'user') {
      setAdminIds(
        isSelected(item)
          ? adminIds.filter((id) => id !== item.id)
          : [...adminIds, item.id],
      )
    } else if (item.type === 'group') {
      setAdminGroupIds(
        isSelected(item)
          ? adminGroupIds.filter((id) => id !== item.id)
          : [...adminGroupIds, item.id],
      )
    } else {
      setAdminRoleIds(
        isSelected(item)
          ? adminRoleIds.filter((id) => id !== item.id)
          : [...adminRoleIds, item.id],
      )
    }
  }

  const selectedItems = useMemo(
    () => pickerItems.filter(isSelected),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [pickerItems, adminIds, adminGroupIds, adminRoleIds],
  )

  const filteredItems = useMemo(() => {
    const search = pickerFilter.toLowerCase().trim()
    if (!search) return pickerItems
    return pickerItems.filter((item) =>
      `${item.label} ${item.sublabel}`.toLowerCase().includes(search),
    )
  }, [pickerItems, pickerFilter])

  useEffect(() => {
    if (!showPicker) return
    const t = setTimeout(() => pickerSearchRef.current?.focus(), 50)
    return () => clearTimeout(t)
  }, [showPicker])

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
    const groupRequests = adminGroupIds.map((groupId) =>
      _data.post(
        `${ProjectApi.api}projects/${projectId}/user-group-permissions/`,
        {
          admin: true,
          group: groupId,
          permissions: [],
        },
      ),
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
    return Promise.all([...userRequests, ...groupRequests, ...roleRequests])
  }

  const close = async (data = {}) => {
    setInterceptClose(null)
    const { environmentId, projectId } = data
    const hasAssignments =
      adminIds.length || adminGroupIds.length || adminRoleIds.length
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
        const showAdminSelector = !!pickerItems.length

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
                  <SettingsButton
                    onClick={() => !disableCreate && setShowPicker(!showPicker)}
                    description='Optionally grant other users, groups, or roles administrator access to this project. Organisation administrators already have full access to all projects.'
                    dropdown={
                      <InlineModal
                        title='Assign administrators'
                        isOpen={showPicker}
                        onClose={() => setShowPicker(false)}
                      >
                        <div style={{ width: 480 }}>
                          <Input
                            ref={(c) => (pickerSearchRef.current = c)}
                            disabled={disableCreate}
                            value={pickerFilter}
                            onChange={(e) =>
                              setPickerFilter(Utils.safeParseEventValue(e))
                            }
                            className='full-width mb-2'
                            placeholder='Search users, groups or roles'
                            search
                          />
                          <div
                            style={{
                              maxHeight: 320,
                              overflowX: 'hidden',
                              overflowY: 'auto',
                            }}
                          >
                            {filteredItems.map((item) => {
                              const selected = isSelected(item)
                              return (
                                <div
                                  key={`${item.type}-${item.id}`}
                                  onClick={() => toggleItem(item)}
                                  className='assignees-list-item clickable'
                                >
                                  <Row
                                    className='flex-nowrap w-100 overflow-hidden overflow-ellipsis'
                                    space
                                  >
                                    <div
                                      className={classNames(
                                        selected ? 'font-weight-bold' : '',
                                        'overflow-ellipsis w-100',
                                      )}
                                    >
                                      {item.label}
                                      <div className='text-muted text-small'>
                                        {item.sublabel}
                                      </div>
                                    </div>
                                    {selected && (
                                      <span className='mr-1'>
                                        <Icon name='checkmark' fill='#6837FC' />
                                      </span>
                                    )}
                                  </Row>
                                </div>
                              )
                            })}
                            {!filteredItems.length && (
                              <div className='text-muted text-center py-2'>
                                No matches
                              </div>
                            )}
                          </div>
                        </div>
                      </InlineModal>
                    }
                    content={
                      <Row style={{ rowGap: '12px' }}>
                        {selectedItems.map((item) => (
                          <Row
                            key={`${item.type}-${item.id}`}
                            onClick={() => toggleItem(item)}
                            className='chip mr-2'
                          >
                            <span className='fw-semibold'>
                              {item.typeLabel}
                            </span>
                            <span className='mx-1'>:</span>
                            <span>{item.label}</span>
                            <span className='chip-icon ion'>
                              <IonIcon icon={closeIcon} />
                            </span>
                          </Row>
                        ))}
                        {!selectedItems.length && (
                          <div className='text-muted'>
                            No project administrators assigned
                          </div>
                        )}
                      </Row>
                    }
                  >
                    Project administrators
                  </SettingsButton>
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
