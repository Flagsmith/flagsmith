import { FC, useEffect, useState } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
  useTestWarehouseConnectionMutation,
  useUpdateWarehouseConnectionMutation,
} from 'common/services/useWarehouseConnection'
import { SnowflakeConfig } from 'common/types/responses'
import WarehouseConnectionCard from './WarehouseConnectionCard'
import WarehouseSetup from './WarehouseSetup'
import WarehouseSetupSkeleton from './WarehouseSetupSkeleton'
import ConfigForm from './ConfigForm'
import sendWarehouseTestEvent from './sendWarehouseTestEvent'
import { getWarehousePollingInterval } from './warehousePolling'

type WarehouseTabProps = {
  environmentId: string
}

const WarehouseTab: FC<WarehouseTabProps> = ({ environmentId }) => {
  const [editing, setEditing] = useState(false)
  const [isEnabling, setIsEnabling] = useState(false)

  const {
    data: connections,
    isError,
    isLoading,
  } = useGetWarehouseConnectionsQuery(
    { environmentId, exclude_event_stats: true },
    { skip: !environmentId },
  )
  const [createConnection, { isLoading: isCreating }] =
    useCreateWarehouseConnectionMutation()
  const [deleteConnection] = useDeleteWarehouseConnectionMutation()
  const [updateConnection] = useUpdateWarehouseConnectionMutation()

  const connection = connections?.[0]
  const connectionId = connection?.id
  const connectionStatus = connection?.status

  const [testConnection, { isLoading: isSendingTestEvent }] =
    useTestWarehouseConnectionMutation()

  useEffect(() => {
    if (connection) setIsEnabling(false)
  }, [connection])

  useEffect(() => {
    const interval = getWarehousePollingInterval(connectionStatus)
    if (!interval || connectionId === undefined) return
    testConnection({ environmentId, id: connectionId })
    const timer = setInterval(() => {
      testConnection({ environmentId, id: connectionId })
    }, interval)
    return () => clearInterval(timer)
  }, [connectionStatus, connectionId, environmentId, testConnection])

  const handleEnableFlagsmith = () => {
    openConfirm({
      body: 'This will enable a Flagsmith Warehouse connection for this environment. Are you sure you want to proceed?',
      onYes: () => {
        setIsEnabling(true)
        createConnection({ environmentId, warehouse_type: 'flagsmith' })
          .unwrap()
          .then(() => toast('Warehouse connection created'))
          .catch(() => {
            setIsEnabling(false)
            toast('Failed to create warehouse connection', 'danger')
          })
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
        <WarehouseSetupSkeleton />
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
          isCreating={isCreating || isEnabling}
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
