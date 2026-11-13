import React, { FC, Ref, useState } from 'react'
import { EditPermissionsModal } from './EditPermissions'
import { Role, User, UserGroupSummary } from 'common/types/responses'
import Tabs from './navigation/TabMenu/Tabs'
import TabItem from './navigation/TabMenu/TabItem'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import RolePermissionsList from './RolePermissionsList'
import ProjectFilter from './ProjectFilter'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetAllEnvironmentsQuery } from 'common/services/useEnvironment'
import { sortEnvironmentsByName } from 'common/utils/sortEnvironmentsByName'
import PlanBasedAccess from './PlanBasedAccess'
import WarningMessage from './WarningMessage'
import EmptyState from './EmptyState'
import Button from './base/forms/Button'
import { useGetProjectsQuery } from 'common/services/useProject'

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
  const {
    data: projects,
    isError: isProjectsError,
    isLoading: isLoadingProjects,
    refetch: refetchProjects,
  } = useGetProjectsQuery(orgId ? { organisationId: orgId } : skipToken)
  const [project, setProject] = useState<string>('')
  const projectId = Number(project) || undefined
  // currentData, not data: data keeps the previous project's list while the next one loads
  const { currentData, isError, isFetching, refetch } =
    useGetAllEnvironmentsQuery(projectId ? { projectId: projectId } : skipToken)
  const environments = currentData && sortEnvironmentsByName(currentData)
  const isLoading = isFetching && !currentData

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
        theme='pill'
        className='m-0'
        isRoles={true}
      >
        <TabItem
          tabLabel={<Row className='justify-content-center'>Organisation</Row>}
          data-test='organisation-permissions-tab'
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
        <TabItem
          tabLabel={<Row className='justify-content-center'>Project</Row>}
          data-test='project-permissions-tab'
        >
          <Row className='justify-content-between'>
            <h5 className='my-3'>Permissions</h5>
            <Input
              type='text'
              className='ml-3'
              value={searchProject}
              onChange={(e) => setSearchProject(Utils.safeParseEventValue(e))}
              size='small'
              placeholder='Search Projects'
              search
            />
          </Row>
          {isLoadingProjects && <Loader />}
          {isProjectsError && !projects && (
            <EmptyState
              status='error'
              title='Could not load projects'
              description='Try again in a few moments.'
              action={
                <Button
                  theme='outline'
                  size='small'
                  onClick={() => refetchProjects()}
                >
                  Try again
                </Button>
              }
            />
          )}
          {!!projects && (
            <RolePermissionsList
              user={user}
              group={group}
              orgId={orgId}
              filter={searchProject}
              mainItems={projects.map((v) => ({
                ...v,
                projectId: v.id,
              }))}
              role={role}
              level={'project'}
              ref={tabRef}
            />
          )}
        </TabItem>
        <TabItem
          tabLabel={<Row className='justify-content-center'>Environment</Row>}
          data-test='environment-permissions-tab'
        >
          <Row className='justify-content-between'>
            <h5 className='my-3'>Permissions</h5>
            <Input
              type='text'
              className='ml-3'
              value={searchEnv}
              onChange={(e) => setSearchEnv(Utils.safeParseEventValue(e))}
              size='small'
              placeholder='Search Environments'
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
          <div className='mt-2'>
            {isLoading && <Loader />}
            {isError && !environments && (
              <EmptyState
                status='error'
                title='Could not load environments'
                description='Try again in a few moments.'
                action={
                  <Button
                    theme='outline'
                    size='small'
                    onClick={() => refetch()}
                  >
                    Try again
                  </Button>
                }
              />
            )}
            {!!environments?.length && (
              <RolePermissionsList
                user={user}
                orgId={orgId}
                group={group}
                filter={searchEnv}
                mainItems={environments.map((v) => {
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
          <p className='text-right mt-5 text-default'>
            This will edit the permissions for{' '}
            <strong>the {group?.name} group</strong>.
          </p>
        </TabItem>
      </Tabs>
    </PlanBasedAccess>
  )
}

export default PermissionsTabs
