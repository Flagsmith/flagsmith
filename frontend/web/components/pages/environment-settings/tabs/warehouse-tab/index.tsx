import { FC, useState } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
  useUpdateWarehouseConnectionMutation,
} from 'common/services/useWarehouseConnection'
import { SnowflakeConfig } from 'common/types/responses'
import Loader from 'components/Loader'
import WarehouseConnectionCard from './WarehouseConnectionCard'
import WarehouseSetup from './WarehouseSetup'
import ConfigForm from './ConfigForm'

type WarehouseTabProps = {
  environmentId: string
}

const WarehouseTab: FC<WarehouseTabProps> = ({ environmentId }) => {
  const [editing, setEditing] = useState(false)

  const {
    data: connections,
    isError,
    isLoading,
  } = useGetWarehouseConnectionsQuery(
    { environmentId },
    { skip: !environmentId },
  )
  const [createConnection, { isLoading: isCreating }] =
    useCreateWarehouseConnectionMutation()
  const [deleteConnection] = useDeleteWarehouseConnectionMutation()
  const [updateConnection] = useUpdateWarehouseConnectionMutation()

  const connection = connections?.[0]

  const handleEnableFlagsmith = () => {
    openConfirm({
      body: 'This will enable a Flagsmith Warehouse connection for this environment. Are you sure you want to proceed?',
      onYes: () => {
        createConnection({ environmentId, warehouse_type: 'flagsmith' })
          .unwrap()
          .then(() => toast('Warehouse connection created'))
          .catch(() => toast('Failed to create warehouse connection', 'danger'))
      },
      title: 'Connect Flagsmith Warehouse',
    })
  }

  const handleCreateSnowflake = (config: SnowflakeConfig) =>
    createConnection({
      config,
      environmentId,
      name: `Snowflake (${config.account_identifier})`,
      warehouse_type: 'snowflake',
    })
      .unwrap()
      .then(() => toast('Warehouse connection created'))

  const handleUpdateSnowflake = (config: SnowflakeConfig) => {
    if (!connection) return Promise.reject()
    return updateConnection({
      config,
      environmentId,
      id: connection.id,
    })
      .unwrap()
      .then(() => {
        setEditing(false)
        toast('Warehouse connection updated')
      })
  }

  const handleDelete = () => {
    if (!connection) return
    deleteConnection({ environmentId, id: connection.id })
      .unwrap()
      .then(() => {
        setEditing(false)
        toast('Warehouse connection removed')
      })
      .catch(() => toast('Failed to remove warehouse connection', 'danger'))
  }

  if (isLoading) {
    return (
      <div className='mt-4 col-md-12'>
        <Loader />
      </div>
    )
  }

  if (isError) {
    return (
      <div className='mt-4 col-md-12'>
        <p className='text-danger'>
          Failed to load warehouse connections. Please try again later.
        </p>
      </div>
    )
  }

  if (!connection) {
    return (
      <div className='mt-4 col-md-12'>
        <WarehouseSetup
          onEnableFlagsmith={handleEnableFlagsmith}
          onCreateSnowflake={handleCreateSnowflake}
          isCreating={isCreating}
        />
      </div>
    )
  }

  if (editing && connection.warehouse_type !== 'flagsmith') {
    return (
      <div className='mt-4 col-md-12'>
        <ConfigForm
          isEdit
          initialConfig={connection.config as SnowflakeConfig}
          onSave={handleUpdateSnowflake}
          onCancel={() => setEditing(false)}
        />
      </div>
    )
  }

  return (
    <div className='mt-4 col-md-12'>
      <WarehouseConnectionCard
        connection={connection}
        onDelete={handleDelete}
        onEdit={
          connection.warehouse_type !== 'flagsmith'
            ? () => setEditing(true)
            : undefined
        }
      />
    </div>
  )
}

WarehouseTab.displayName = 'WarehouseTab'
export default WarehouseTab
