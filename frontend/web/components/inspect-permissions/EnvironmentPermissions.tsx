import ExpandablePermissionsList from './ExpandablePermissionsList'
import { useEnvironmentsByName } from 'common/hooks/useEnvironmentsByName'
import ErrorMessage from 'components/ErrorMessage'
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
  const { environments, isError, isLoading } = useEnvironmentsByName(
    Number(projectId) || undefined,
  )

  const filteredEnvironments = environments?.filter((v) => {
    const search = searchEnvironment?.toLowerCase()
    if (!search) return true
    return `${v.name}`.toLowerCase().includes(search)
  })
  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }
  if (isError) {
    return (
      <ErrorMessage error='Could not load environments for this project.' />
    )
  }
  if (!environments?.length) {
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
            projectId={Number(projectId)}
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
