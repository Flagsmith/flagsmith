import React, { FC, Ref, useEffect, useState } from 'react'
import { EditPermissionsModal } from './EditPermissions'
import {
  Environment,
  Project,
  Role,
  User,
  UserGroupSummary,
} from 'common/types/responses'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import RolePermissionsList from './RolePermissionsList'
import ProjectFilter from './ProjectFilter'
import OrganisationStore from 'common/stores/organisation-store'
import AddEditTags from './tags/AddEditTags'
import InputGroup from './base/forms/InputGroup'
import Button from './base/forms/Button'
import InfoMessage from './InfoMessage'
import { useGetRoleQuery, useUpdateRoleMutation } from 'common/services/useRole'
import PlanBasedAccess from './PlanBasedAccess'
import WarningMessage from './WarningMessage'

type PermissionsTabsType = {
  orgId?: number
  group?: UserGroupSummary
  user?: User
  role?: Role | undefined
  value?: number
  onChange?: (v: number) => void
  uncontrolled?: boolean
  tabRef?: Ref<any>
}

const PermissionsTabs: FC<PermissionsTabsType> = ({
  group,
  onChange,
  orgId,
  role,
  tabRef,
  uncontrolled,
  user,
  value,
}) => {
  const { data: roleData } = useGetRoleQuery(
    {
      organisation_id: role?.organisation as any,
      role_id: role?.id as any,
    },
    { skip: !role || !orgId },
  )
  const [searchProject, setSearchProject] = useState<string>('')
  const [searchEnv, setSearchEnv] = useState<string>('')
  const projectData: Project[] = OrganisationStore.getProjects()
  const [project, setProject] = useState<string>('')
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [tags, setTags] = useState<number[]>(roleData?.tags || [])
  const [projectWithTags, setProjectWithTags] = useState<number[]>([])
  const [roleTagsChanged, setRoleTagsChanged] = useState<boolean>(false)
  const [hasTags, setHasTags] = useState<boolean>(
    !!roleData?.tags.length || false,
  )
  const [editRole] = useUpdateRoleMutation()

  useEffect(() => {
    if (project && projectData) {
      const environments = projectData.find(
        (p) => p.id === parseInt(project),
      )?.environments
      setEnvironments(environments || [])
    }
  }, [project, projectData])

  if (!orgId) {
    return
  }

  const deprecationMessage = (
    <div>
      Group-level permissions are deprecated. Assign{' '}
      <a href='?type=roles' target='_blank'>
        roles
      </a>{' '}
      to this group instead.{' '}
      <a
        href='https://docs.flagsmith.com/system-administration/rbac#deprecated-features'
        target='_blank'
        rel='noreferrer'
      >
        Learn more
      </a>
      .
    </div>
  )

  return (
    <PlanBasedAccess feature={'RBAC'} theme={'page'}>
      {!!group && <WarningMessage warningMessage={deprecationMessage} />}
      <Tabs
        uncontrolled={uncontrolled}
        value={value}
        onChange={onChange}
        theme='pill m-0'
        isRoles={true}
      >
        {roleData && (
          <TabItem
            tabLabel={<Row className='justify-content-center'>Tags</Row>}
          >
            <FormGroup className='mt-3 setting'>
              <InputGroup
                title={<h5>Permission Tags</h5>}
                unsaved={roleTagsChanged}
                component={
                  <>
                    <InfoMessage>
                      When applying tags to a role, the delete feature and
                      update feature state permissions will only be valid for
                      features sharing the same tag, providing more granularity.{' '}
                      <Button
                        theme='text'
                        target='_blank'
                        href='http://localhost:3000/system-administration/rbac#tags'
                        className='fw-normal'
                      >
                        Learn more.
                      </Button>
                    </InfoMessage>

                    <div className='mb-2' style={{ width: 250 }}>
                      <ProjectFilter
                        organisationId={orgId}
                        onChange={(p) => {
                          setProject(p)
                        }}
                        value={project}
                      />
                    </div>
                    {project && (
                      <AddEditTags
                        readOnly={false}
                        projectId={`${project}`}
                        value={tags}
                        onChange={(tags) => {
                          setRoleTagsChanged(true)
                          setTags(tags)
                          setProjectWithTags([
                            ...projectWithTags,
                            parseInt(project),
                          ])
                        }}
                      />
                    )}
                  </>
                }
              />
            </FormGroup>
            <Button
              onClick={() => {
                editRole({
                  body: {
                    description: roleData!.description!,
                    name: roleData!.name,
                    tags: tags,
                  },
                  organisation_id: orgId,
                  role_id: roleData!.id!,
                }).then((res) => {
                  if (res.data?.tags?.length === 0) {
                    setHasTags(false)
                  } else {
                    setHasTags(true)
                  }
                  setRoleTagsChanged(false)
                  toast('Tags added successfully')
                })
              }}
            >
              Save Tags
            </Button>
          </TabItem>
        )}

        {!hasTags && (
          <TabItem
            tabLabel={
              <Row className='justify-content-center'>Organisation</Row>
            }
          >
            <EditPermissionsModal
              id={orgId}
              group={group}
              isGroup={!!group}
              user={user}
              className='mt-2'
              level={'organisation'}
              role={role}
            />
          </TabItem>
        )}
        <TabItem
          tabLabel={<Row className='justify-content-center'>Project</Row>}
        >
          <Row className='justify-content-between'>
            <h5 className='my-3'>Permissions</h5>
            <Input
              type='text'
              className='ml-3'
              value={searchProject}
              onChange={(e: InputEvent) =>
                setSearchProject(Utils.safeParseEventValue(e))
              }
              size='small'
              placeholder='Search'
              search
            />
          </Row>
          <RolePermissionsList
            user={user}
            group={group}
            orgId={orgId}
            filter={searchProject}
            mainItems={projectData}
            role={role}
            hasTags={tags.length !== 0}
            level={'project'}
            ref={tabRef}
          />
        </TabItem>
        <TabItem
          tabLabel={<Row className='justify-content-center'>Environment</Row>}
        >
          <Row className='justify-content-between'>
            <h5 className='my-3'>Permissions</h5>
            <Input
              type='text'
              className='ml-3'
              value={searchEnv}
              onChange={(e: InputEvent) =>
                setSearchEnv(Utils.safeParseEventValue(e))
              }
              size='small'
              placeholder='Search'
              search
            />
          </Row>
          <div className='mb-2' style={{ width: 250 }}>
            <ProjectFilter
              organisationId={orgId}
              onChange={setProject}
              value={project}
            />
          </div>
          {environments.length > 0 && (
            <RolePermissionsList
              user={user}
              orgId={orgId}
              group={group}
              filter={searchEnv}
              mainItems={(environments || [])?.map((v) => {
                return {
                  id: role ? v.id : v.api_key,
                  name: v.name,
                }
              })}
              role={role}
              hasTags={tags.length !== 0}
              level={'environment'}
              ref={tabRef}
            />
          )}
        </TabItem>
      </Tabs>
    </PlanBasedAccess>
  )
}

export default PermissionsTabs
