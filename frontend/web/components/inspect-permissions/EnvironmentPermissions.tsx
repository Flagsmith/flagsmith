import { useMemo } from 'react'
import ExpandablePermissionsList from './ExpandablePermissionsList'
import OrganisationStore from 'common/stores/organisation-store'
import { Project } from 'common/types/responses'
import PanelSearch from 'components/PanelSearch'

type EnvironmentPermissionsProps = {
  projectId?: string
  searchEnvironment?: string
  userId?: number
}

const EnvironmentPermissions = ({
  projectId,
  searchEnvironment = '',
  userId,
}: EnvironmentPermissionsProps) => {
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

export type { EnvironmentPermissionsProps }
export default EnvironmentPermissions
