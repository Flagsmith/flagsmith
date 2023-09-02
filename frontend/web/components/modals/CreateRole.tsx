import React, {
  FC,
  useEffect,
  useState,
  useRef,
  forwardRef,
  useImperativeHandle,
} from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import CollapsibleNestedList from 'components/CollapsibleNestedList'
import {
  useGetRoleQuery,
  useCreateRoleMutation,
  useUpdateRoleMutation,
} from 'common/services/useRole'

import { EditPermissionsModal } from 'components/EditPermissions'
import OrganisationStore from 'common/stores/organisation-store'
import ProjectFilter from 'components/ProjectFilter'
import { Environment } from 'common/types/responses'
import { setInterceptClose } from 'components/modals/base/ModalDefault'

type CreateRoleType = {
  organisationId?: string
  role: Role
  onComplete: () => void
  isEdit?: boolean
}
const CreateRole: FC<CreateRoleType> = ({
  isEdit,
  onComplete,
  organisationId,
  role,
}) => {
  const buttonText = isEdit ? 'Update Role' : 'Create Role'
  const [tab, setTab] = useState<number>(0)
  const [project, setProject] = useState<string>('')
  const [environments, setEnvironments] = useState<Environment[]>([])

  const projectData = OrganisationStore.getProjects()

  useEffect(() => {
    if (project) {
      const environments = projectData.find(
        (p) => p.id === parseInt(project),
      ).environments
      setEnvironments(environments)
    }
  }, [project, projectData])

  const Tab1 = forwardRef((props, ref) => {
    const { data: roleData, isLoading } = useGetRoleQuery(
      {
        organisation_id: role?.organisation,
        role_id: role?.id,
      },
      { skip: !role },
    )
    const [roleName, setRoleName] = useState<string>('')
    const [roleDesc, setRoleDesc] = useState<string>('')
    const [isSaving, setIsSaving] = useState<boolean>(false)
    const [roleNameChanged, setRoleNameChanged] = useState<boolean>(false)
    const [roleDescChanged, setRoleDescChanged] = useState<boolean>(false)

    useImperativeHandle(
      ref,
      () => {
        return {
          onClosing() {
            if (roleNameChanged || roleDescChanged) {
              return new Promise((resolve) => {
                openConfirm(
                  'Are you sure?',
                  'Closing this will discard your unsaved changes.',
                  () => resolve(true),
                  () => resolve(false),
                  'Ok',
                  'Cancel',
                )
              })
            } else {
              return Promise.resolve(true)
            }
          },
          tabChanged() {
            return roleNameChanged || roleDescChanged
          },
        }
      },
      [roleNameChanged, roleDescChanged],
    )
    useEffect(() => {
      if (!isLoading && isEdit && roleData) {
        setRoleName(roleData.name)
        setRoleDesc(roleData.description)
      }
    }, [roleData, isLoading])

    const [createRole, { isSuccess: createSuccess }] = useCreateRoleMutation()

    const [editRole, { isSuccess: updateSuccess }] = useUpdateRoleMutation()

    useEffect(() => {
      if (createSuccess || updateSuccess) {
        setRoleNameChanged(false)
        setRoleDescChanged(false)
        setIsSaving(false)
        onComplete?.()
      }
    }, [createSuccess, updateSuccess])

    const save = () => {
      if (isEdit) {
        editRole({
          body: { description: roleDesc, name: roleName },
          organisation_id: role.organisation,
          role_id: role.id,
        })
      } else {
        createRole({
          description: roleDesc,
          name: roleName,
          organisation_id: organisationId,
        })
      }
    }

    return isLoading ? (
      <div className='text-center'>
        <Loader />
      </div>
    ) : (
      <div className='my-4'>
        <InputGroup
          title='Role name'
          inputProps={{
            className: 'full-width',
            name: 'roleName',
          }}
          value={roleName}
          unsaved={isEdit && roleNameChanged}
          onChange={(event) => {
            setRoleNameChanged(true)
            setRoleName(Utils.safeParseEventValue(event))
          }}
          id='roleName'
          placeholder='E.g. Viewers'
        />
        <InputGroup
          title='Role Description'
          inputProps={{
            className: 'full-width',
            name: 'description',
          }}
          value={roleDesc}
          unsaved={isEdit && roleDescChanged}
          onChange={(event) => {
            setRoleDescChanged(true)
            setRoleDesc(Utils.safeParseEventValue(event))
          }}
          id='description'
          placeholder='E.g. Some role description'
        />
        <div className='text-right mb-2'>
          <Button
            onClick={() => save()}
            data-test='update-role-btn'
            id='update-role-btn'
            disabled={isSaving || !roleName}
          >
            {isSaving && isEdit
              ? 'Updating'
              : isSaving && !isEdit
              ? 'Creating'
              : buttonText}
          </Button>
        </div>
      </div>
    )
  })

  const TabValue = () => {
    const ref = useRef(null)
    const ref2 = useRef(null)
    useEffect(() => {
      if (isEdit) {
        setInterceptClose(() => ref.current.onClosing())
      }
    }, [])

    const changeTab = (newTab) => {
      const changed = ref.current.tabChanged()
      if (changed && newTab !== tab) {
        return new Promise((resolve) => {
          openConfirm(
            'Are you sure?',
            'Changing this tab will discard your unsaved changes.',
            () => {
              resolve(true), setTab(newTab)
            },
            () => resolve(false),
            'Ok',
            'Cancel',
          )
        })
      } else {
        setTab(newTab)
      }
    }

    return isEdit ? (
      <Tabs value={tab} onChange={changeTab} buttonTheme='text'>
        <TabItem tabLabel={<Row className='justify-content-center'>Role</Row>}>
          <Tab1 ref={ref} />
        </TabItem>
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>
              Organisation permissions
            </Row>
          }
        >
          <EditPermissionsModal level={'organisation'} role={role} ref={ref2} />
        </TabItem>
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>Project permissions</Row>
          }
        >
          <h5 className='my-4 title'>Edit Permissions</h5>
          <CollapsibleNestedList
            mainItems={projectData}
            role={role}
            level={'project'}
            ref={ref}
          />
        </TabItem>
        <TabItem
          tabLabel={
            <Row className='justify-content-center'>
              Environment permissions
            </Row>
          }
        >
          <h5 className='my-4 title'>Edit Permissions</h5>
          <ProjectFilter
            organisationId={role.organisation}
            onChange={setProject}
            value={project}
            className='mb-2'
          />
          {environments.length > 0 && (
            <CollapsibleNestedList
              mainItems={environments}
              role={role}
              level={'environment'}
              ref={ref}
            />
          )}
        </TabItem>
      </Tabs>
    ) : (
      <div className='my-3 mx-4'>
        <Tab1 />
      </div>
    )
  }

  return (
    <div id='create-feature-modal'>
      <TabValue />
    </div>
  )
}
export default CreateRole
module.exports = CreateRole
