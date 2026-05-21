import { FC } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
  useUpdateWarehouseConnectionMutation,
} from 'common/services/useWarehouseConnection'
import { WarehouseConnection } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Setting from 'components/Setting'
import WarehouseConnectionCard from './WarehouseConnectionCard'
import CreateWarehouseConnectionModal from './CreateWarehouseConnectionModal'

type WarehouseTabProps = {
  environmentId: string
}

const WarehouseTab: FC<WarehouseTabProps> = ({ environmentId }) => {
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

  const hasFlagsmithConnection = connections?.some(
    (c) => c.warehouse_type === 'flagsmith',
  )
  const hasConnections = !!connections?.length

  const handleCreateFlagsmith = () => {
    createConnection({
      environmentId,
      warehouse_type: 'flagsmith',
    })
      .unwrap()
      .then(() => toast('Warehouse connection created'))
      .catch(() => toast('Failed to create warehouse connection', 'danger'))
  }

  const handleConfirmFlagsmith = () => {
    openConfirm({
      body: 'This will enable a Flagsmith Warehouse connection for this environment. Are you sure you want to proceed?',
      onYes: handleCreateFlagsmith,
      title: 'Connect Flagsmith Warehouse',
    })
  }

  const handleOpenCreateDrawer = () => {
    openModal(
      'Connect Warehouse',
      <CreateWarehouseConnectionModal
        save={(data) => createConnection({ environmentId, ...data }).unwrap()}
      />,
      'side-modal side-modal--narrow',
    )
  }

  const handleOpenEditDrawer = (connection: WarehouseConnection) => {
    openModal(
      'Edit Warehouse',
      <CreateWarehouseConnectionModal
        connection={connection}
        save={(data) =>
          updateConnection({
            environmentId,
            id: connection.id,
            ...data,
          }).unwrap()
        }
      />,
      'side-modal side-modal--narrow',
    )
  }

  const handleDelete = (connection: WarehouseConnection) => {
    deleteConnection({ environmentId, id: connection.id })
      .unwrap()
      .then(() => toast('Warehouse connection removed'))
      .catch(() => toast('Failed to remove warehouse connection', 'danger'))
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

  return (
    <div className='mt-4 col-md-12 d-flex flex-column gap-5'>
      {!hasFlagsmithConnection && (
        <div>
          <Setting
            title='Connect Flagsmith Warehouse'
            description='Enable a hosted warehouse connection for this environment to collect experimentation data.'
            checked={false}
            disabled={isLoading || isCreating}
            onChange={handleConfirmFlagsmith}
          />
        </div>
      )}
      <div>
        {hasConnections ? (
          <>
            <div className='d-flex justify-content-end mb-3'>
              <Button onClick={handleOpenCreateDrawer} size='small'>
                Configure a warehouse
              </Button>
            </div>
            {connections.map((connection) => (
              <WarehouseConnectionCard
                key={connection.id}
                connection={connection}
                onDelete={() => handleDelete(connection)}
                onEdit={
                  connection.warehouse_type !== 'flagsmith'
                    ? () => handleOpenEditDrawer(connection)
                    : undefined
                }
              />
            ))}
          </>
        ) : (
          <div>
            <h5 className='fw-bold'>Connect an external Warehouse</h5>
            <p className='text-muted mb-3'>
              Flagsmith lets you connect your own data warehouse to collect
              experimentation data.
            </p>
            <Button onClick={handleOpenCreateDrawer} size='small'>
              Configure a warehouse
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

WarehouseTab.displayName = 'WarehouseTab'
export default WarehouseTab
