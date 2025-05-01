import React, { FC, Ref, useMemo, useState } from 'react'
import {
  AvailablePermission,
  Project,
  Role,
  User,
  UserGroupSummary,
} from 'common/types/responses'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import ProjectFilter from './ProjectFilter'
import OrganisationStore from 'common/stores/organisation-store'
import PlanBasedAccess from './PlanBasedAccess'
import { PermissionLevel } from 'common/types/requests'
import { useGetUserPermissionsQuery } from 'common/services/useUserPermissions'
import PanelSearch from './PanelSearch'
import Format from 'common/utils/format'

import { PermissionRow } from './PermissionRow'
import { useGetAvailablePermissionsQuery } from 'common/services/useAvailablePermissions'

import BooleanDotIndicator from './BooleanDotIndicator'
import Icon from './Icon'
import DerivedPermissionsList from './DerivedPermissionsList'

type InspectPermissionsType = {
  orgId?: number
  group?: UserGroupSummary
  user?: User
  role?: Role | undefined
  value?: number
  onChange?: (v: number) => void
  uncontrolled?: boolean
  tabRef?: Ref<any>
}

type ExpandablePermissionsListProps<T> = {
  item: T
  level: PermissionLevel
  userId?: number
  projectId?: number
  getItemName: (item: T) => string
  getItemId: (item: T) => string | number
  getLevelId: (item: T) => string
  showSearch?: boolean
}

const Permissions = ({
  level,
  levelId,
  projectId,
  userId,
}: {
  level: PermissionLevel
  levelId: string
  userId?: number
  projectId?: number
  className?: string
}) => {
  const { data: userPermissions, isLoading: isLoadingPermissions } =
    useGetUserPermissionsQuery(
      { id: levelId, level, userId: userId },
      { refetchOnMountOrArgChange: true, skip: !level || !levelId || !userId },
    )

  const { data: permissions } = useGetAvailablePermissionsQuery({ level })

  if (
    !userPermissions ||
    !userPermissions.permissions ||
    !permissions ||
    isLoadingPermissions
  ) {
    return (
      <div className='modal-body text-center'>
        <Loader />
      </div>
    )
  }

  const isAdmin = userPermissions.admin
  const isDerivedAdmin =
    userPermissions.admin && userPermissions.is_directly_granted === false

  return (
    <div>
      {level !== 'organisation' && (
        <div className='my-2'>
          <Row>
            <Flex>
              <div className='font-weight-medium text-dark mb-1'>
                Administrator
              </div>
              {isDerivedAdmin && (
                <div>
                  <DerivedPermissionsList
                    derivedPermissions={userPermissions.derived_from}
                  />
                </div>
              )}
            </Flex>
            <div className='mr-3'>
              <BooleanDotIndicator enabled={isAdmin} />
            </div>
          </Row>
        </div>
      )}
      <PanelSearch
        filterRow={(item: AvailablePermission, search: string) => {
          const name = Format.enumeration.get(item.key).toLowerCase()
          return name.includes(search?.toLowerCase() || '')
        }}
        title='Permissions'
        className='no-pad mb-2 overflow-visible'
        items={permissions}
        renderRow={(p) => (
          <PermissionRow
            key={p.key}
            permission={p}
            level={level}
            projectId={projectId}
            entityPermissions={userPermissions}
            isAdmin={isAdmin}
            isTagBasedPermissions={false}
            onValueChanged={() => {}}
            onSelectPermissions={() => {}}
            onTogglePermission={() => {}}
            isDebug
          />
        )}
      />
    </div>
  )
}

const ExpandablePermissionsList = <T,>({
  getItemId,
  getItemName,
  getLevelId,
  item,
  level,
  projectId,
  userId,
}: ExpandablePermissionsListProps<T>) => {
  const [expandedItems, setExpandedItems] = useState<(string | number)[]>([])

  const toggleExpand = async (id: string | number) => {
    setExpandedItems((prevExpanded) =>
      prevExpanded.includes(id)
        ? prevExpanded.filter((item) => item !== id)
        : [...prevExpanded, id],
    )
  }

  return (
    <div
      className='list-item d-flex flex-column justify-content-center py-2 list-item-sm clickable'
      data-test={`permissions-${getItemName(item).toLowerCase()}`}
      key={getItemId(item)}
    >
      <Row
        className='px-3 flex-fill align-items-center user-select-none clickable'
        onClick={() => toggleExpand(getItemId(item))}
      >
        <Flex>
          <div className={'list-item-subtitle'}>
            <strong>{getItemName(item)}</strong>{' '}
          </div>
        </Flex>
        <div>
          <Icon
            fill={'#9DA4AE'}
            name={
              expandedItems.includes(getItemId(item))
                ? 'chevron-down'
                : 'chevron-right'
            }
          />
        </div>
      </Row>
      <div>
        {expandedItems.includes(getItemId(item)) && (
          <div className='modal-body px-3'>
            <Permissions
              level={level}
              levelId={getLevelId(item)}
              userId={userId}
              projectId={projectId}
            />
          </div>
        )}
      </div>
    </div>
  )
}

const EnvironmentPermissions = ({
  projectId,
  searchEnvironment = '',
  userId,
}: {
  userId?: number
  projectId?: string
  searchEnvironment?: string
}) => {
  const projectData: Project[] = OrganisationStore.getProjects()

  const environments = useMemo(() => {
    if (!projectData || !projectId) {
      return
    }
    return projectData.find((p) => p.id === parseInt(projectId))?.environments
  }, [projectData, projectId])

  const filteredEnvironments = environments?.filter((v) => {
    const search = searchEnvironment?.toLowerCase()
    if (!search) return true
    return `${v.name}`.toLowerCase().includes(search)
  })

  return (
    <>
      <PanelSearch
        header={
          <Row className='table-header'>
            <Flex className='px-3'>Name</Flex>
          </Row>
        }
        className='no-pad'
        items={filteredEnvironments}
        renderRow={(env) => (
          <ExpandablePermissionsList
            key={env.id}
            item={env}
            level='environment'
            userId={userId}
            projectId={parseInt(projectId ?? '')}
            getItemName={(env) => env.name}
            getItemId={(env) => env.id}
            getLevelId={(env) => env.api_key}
          />
        )}
      />
    </>
  )
}

const ProjectPermissions = ({ userId }: { userId?: number }) => {
  const projectData: Project[] = OrganisationStore.getProjects()
  const [searchProject, setSearchProject] = useState<string>('')

  const filteredProjects =
    projectData &&
    projectData?.filter((v) => {
      const search = searchProject?.toLowerCase()
      if (!search) return true
      return `${v.name}`.toLowerCase().includes(search)
    })

  return (
    <>
      <Row className='justify-content-between'>
        <h5 className='my-3'>Permissions</h5>
        <Input
          type='text'
          className='ml-3='
          value={searchProject}
          onChange={(e: InputEvent) => {
            setSearchProject(Utils.safeParseEventValue(e))
          }}
          size='small'
          placeholder='Search Projects'
          search
        />
      </Row>
      <PanelSearch
        header={
          <Row className='table-header'>
            <Flex className='px-3'>Name</Flex>
          </Row>
        }
        className='no-pad'
        items={filteredProjects}
        renderRow={(project) => (
          <ExpandablePermissionsList
            key={project.id}
            item={project}
            level='project'
            userId={userId}
            projectId={project.id}
            getItemName={(project) => project.name}
            getItemId={(project) => project.id}
            getLevelId={(project) => String(project.id)}
          />
        )}
      />
    </>
  )
}

const InspectPermissions: FC<InspectPermissionsType> = ({
  onChange,
  orgId,
  uncontrolled,
  user,
  value,
}) => {
  const [searchEnv, setSearchEnv] = useState<string>('')
  const projectData: Project[] = OrganisationStore.getProjects()
  const [project, setProject] = useState<string>('')

  const environments = useMemo(() => {
    if (!project || !projectData) {
      return null
    }
    return projectData.find((p) => p.id === parseInt(project))?.environments
  }, [project, projectData])

  if (!orgId) {
    return null
  }

  return (
    <PlanBasedAccess feature={'RBAC'} theme={'page'}>
      <Tabs
        uncontrolled={uncontrolled}
        value={value}
        onChange={onChange}
        theme='pill m-0'
        isRoles={true}
      >
        <TabItem
          tabLabel={<Row className='justify-content-center'>Organisation</Row>}
          data-test='organisation-permissions-tab'
        >
          <div className='my-2'>
            <Permissions
              level='organisation'
              levelId={String(orgId)}
              userId={user?.id}
            />
          </div>
        </TabItem>
        <TabItem
          tabLabel={<Row className='justify-content-center'>Project</Row>}
          data-test='project-permissions-tab'
        >
          <ProjectPermissions userId={user?.id} />
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
              onChange={(e: InputEvent) =>
                setSearchEnv(Utils.safeParseEventValue(e))
              }
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
            {environments?.length !== 0 && (
              <EnvironmentPermissions
                userId={user?.id}
                projectId={project}
                searchEnvironment={searchEnv}
              />
            )}
          </div>
        </TabItem>
      </Tabs>
    </PlanBasedAccess>
  )
}

export default InspectPermissions
