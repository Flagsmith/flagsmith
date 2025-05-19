import React, { FC, Ref, useMemo, useState } from 'react'
import { Project, Role, User, UserGroupSummary } from 'common/types/responses'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import ProjectFilter from 'components/ProjectFilter'
import OrganisationStore from 'common/stores/organisation-store'
import PlanBasedAccess from 'components/PlanBasedAccess'
import Permissions from './Permissions'
import ProjectPermissions from './ProjectPermissions'
import EnvironmentPermissions from './EnvironmentPermissions'

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

export type { InspectPermissionsType }
export default InspectPermissions
