import ExpandablePermissionsList from './ExpandablePermissionsList'
import { skipToken } from '@reduxjs/toolkit/query'
import { useGetAllEnvironmentsQuery } from 'common/services/useEnvironment'
import { sortEnvironmentsByName } from 'common/utils/sortEnvironmentsByName'
import EmptyState from 'components/EmptyState'
import Button from 'components/base/forms/Button'
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
  const id = Number(projectId) || undefined
  // currentData, not data: data keeps the previous project's list while the next one loads
  const { currentData, isError, isFetching, refetch } =
    useGetAllEnvironmentsQuery(id ? { projectId: id } : skipToken)
  const environments = currentData && sortEnvironmentsByName(currentData)
  const isLoading = isFetching && !currentData

  const filteredEnvironments = environments?.filter((v) => {
    const search = searchEnvironment?.toLowerCase()
    if (!search) return true
    return `${v.name}`.toLowerCase().includes(search)
  })
  if (isLoading) {
    return <Loader />
  }
  if (isError && !environments) {
    return (
      <EmptyState
        status='error'
        title='Could not load environments'
        description='Try again in a few moments.'
        action={
          <Button theme='outline' size='small' onClick={() => refetch()}>
            Try again
          </Button>
        }
      />
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
