import React, { useEffect, useMemo, useRef, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import { setInterceptClose } from './base/ModalDefault'
import PlanBasedAccess from 'components/PlanBasedAccess'
import UserSelect from 'components/UserSelect'
import { useGetUsersQuery } from 'common/services/useUser'
import AccountStore from 'common/stores/account-store'
import getUserDisplayName from 'common/utils/getUserDisplayName'
import _data from 'common/data/base/_data'
import ProjectApi from 'common/project'

const CreateProject = ({ history, onSave }) => {
  const [name, setName] = useState('')
  const [adminIds, setAdminIds] = useState([])
  const [showUsers, setShowUsers] = useState(false)
  const [assigningAdmins, setAssigningAdmins] = useState(false)
  const inputRef = useRef(null)

  const organisationId = AccountStore.getOrganisation()?.id
  const currentUserId = AccountStore.getUser()?.id
  const { data: users } = useGetUsersQuery(
    { organisationId },
    { skip: !organisationId },
  )

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

  const assignProjectAdmins = (projectId) =>
    Promise.all(
      adminIds.map((userId) =>
        _data.post(`${ProjectApi.api}projects/${projectId}/user-permissions/`, {
          admin: true,
          permissions: [],
          user: userId,
        }),
      ),
    )

  const close = async (data = {}) => {
    setInterceptClose(null)
    const { environmentId, projectId } = data
    if (projectId && adminIds.length) {
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
        const showAdminSelector = !!eligibleAdmins.length

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
                  <div className='text-muted text-small mb-2'>
                    Organisation administrators already have full access to all
                    projects. Optionally grant other users administrator access
                    to this project.
                  </div>
                  <Row>
                    {selectedAdmins.map((u) => (
                      <Row
                        key={u.id}
                        onClick={() =>
                          setAdminIds(adminIds.filter((id) => id !== u.id))
                        }
                        className='chip'
                        style={{ marginBottom: 4, marginTop: 4 }}
                      >
                        <span className='font-weight-bold'>
                          {getUserDisplayName(u)}
                        </span>
                        <span className='chip-icon ion'>
                          <IonIcon icon={closeIcon} />
                        </span>
                      </Row>
                    ))}
                    <Button
                      type='button'
                      theme='text'
                      disabled={disableCreate}
                      onClick={() => setShowUsers(true)}
                    >
                      Add administrator
                    </Button>
                  </Row>
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
