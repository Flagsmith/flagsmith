import { FC, useEffect, useState } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
  useTestWarehouseConnectionMutation,
  useUpdateWarehouseConnectionMutation,
} from 'common/services/useWarehouseConnection'
import { SnowflakeConfig } from 'common/types/responses'
import Loader from 'components/Loader'
import WarehouseConnectionCard from './WarehouseConnectionCard'
import WarehouseSetup from './WarehouseSetup'
import ConfigForm from './ConfigForm'
import sendWarehouseTestEvent from './sendWarehouseTestEvent'
import { getWarehousePollingInterval } from './warehousePolling'

type WarehouseTabProps = {
  environmentId: string
}

const WarehouseTab: FC<WarehouseTabProps> = ({ environmentId }) => {
  const [editing, setEditing] = useState(false)

  // Poll only while waiting for the first event to land in the warehouse. Held
  // in state (updated by the effect below) because the interval depends on the
  // query's own result, which isn't available when the hook is first called.
  const [pollingInterval, setPollingInterval] = useState(0)

  const {
    data: connections,
    isError,
    isLoading,
  } = useGetWarehouseConnectionsQuery(
    { environmentId },
    { pollingInterval, skip: !environmentId },
  )
  const [createConnection, { isLoading: isCreating }] =
    useCreateWarehouseConnectionMutation()
  const [deleteConnection] = useDeleteWarehouseConnectionMutation()
  const [updateConnection] = useUpdateWarehouseConnectionMutation()

  const connection = connections?.[0]

  useEffect(() => {
    setPollingInterval(getWarehousePollingInterval(connection?.status))
  }, [connection?.status])

  const [testConnection, { isLoading: isSendingTestEvent }] =
    useTestWarehouseConnectionMutation()

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

  const handleCreateSnowflake = ({
    name,
    ...config
  }: SnowflakeConfig & { name: string }) =>
    createConnection({
      config,
      environmentId,
      name,
      warehouse_type: 'snowflake',
    })
      .unwrap()
      .then(() => toast('Warehouse connection created'))

  const handleUpdateSnowflake = ({
    name,
    ...config
  }: SnowflakeConfig & { name: string }) => {
    if (!connection) return Promise.reject()
    return updateConnection({
      config,
      environmentId,
      id: connection.id,
      name,
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

  const handleSendTestEvent = () => {
    if (!connection) return
    sendWarehouseTestEvent(environmentId)
      .then(() => testConnection({ environmentId, id: connection.id }).unwrap())
      .then(() => toast('Test event sent'))
      .catch((error) => {
        // eslint-disable-next-line no-console
        console.error('[warehouse] send test event failed:', error)
        toast('Failed to send test event', 'danger')
      })
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

  if (editing && connection.warehouse_type === 'snowflake') {
    return (
      <div className='mt-4 col-md-12'>
        <ConfigForm
          isEdit
          initialConfig={connection.config as SnowflakeConfig}
          initialName={connection.name}
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
        onSendTestEvent={handleSendTestEvent}
        isSendingTestEvent={isSendingTestEvent}
      />
    </div>
  )
}

WarehouseTab.displayName = 'WarehouseTab'
export default WarehouseTab
