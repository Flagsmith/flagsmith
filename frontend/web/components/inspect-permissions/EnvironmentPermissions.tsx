import { useMemo } from 'react'
import sortBy from 'lodash/sortBy'
import ExpandablePermissionsList from './ExpandablePermissionsList'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
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
  const { data } = useGetEnvironmentsQuery(
    { projectId: parseInt(projectId ?? '') },
    { skip: !projectId },
  )
  const environments = useMemo(
    () => data && sortBy(data.results, 'name'),
    [data],
  )

  const filteredEnvironments = environments?.filter((v) => {
    const search = searchEnvironment?.toLowerCase()
    if (!search) return true
    return `${v.name}`.toLowerCase().includes(search)
  })
  if (environments?.length === 0) {
    return null
  }
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

export default EnvironmentPermissions
