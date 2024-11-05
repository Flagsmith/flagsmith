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
import PlanBasedAccess from './PlanBasedAccess'
import WarningMessage from './WarningMessage'
import TagBasedPermissions from './TagBasedPermissions'

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
  const [searchProject, setSearchProject] = useState<string>('')
  const [searchEnv, setSearchEnv] = useState<string>('')
  const projectData: Project[] = OrganisationStore.getProjects()
  const [project, setProject] = useState<string>('')
  const [environments, setEnvironments] = useState<Environment[]>([])

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
        {role?.tag_based !== true && (
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
            mainItems={projectData.map((v) => ({ ...v, projectId: v.id }))}
            role={role}
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
          <div className='my-4'>
            <TagBasedPermissions projectId={project} role={role} />
          </div>
          <div className='mt-2'>
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
                    parentId: v.project,
                  }
                })}
                role={role}
                level={'environment'}
                ref={tabRef}
              />
            )}
          </div>
        </TabItem>
      </Tabs>
    </PlanBasedAccess>
  )
}

export default PermissionsTabs
