import React, { FC } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
} from 'common/services/useWarehouseConnection'
import Loader from 'components/Loader'
import Setting from 'components/Setting'
import WarehouseConnectionCard from './WarehouseConnectionCard'

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

  const hasNoConnection = !connections || connections.length === 0

  if (hasNoConnection) {
    return (
      <div className='mt-4 col-md-12'>
        <Setting
          title='Connect Flagsmith Warehouse'
          description='Enable a hosted warehouse connection for this environment to collect experimentation data.'
          checked={false}
          disabled={isLoading || isCreating}
          onChange={() =>
            openConfirm({
              body: 'This will enable a Flagsmith Warehouse connection for this environment. Are you sure you want to proceed?',
              onYes: () =>
                createConnection({
                  environmentId,
                  warehouse_type: 'flagsmith',
                })
                  .unwrap()
                  .then(() => toast('Warehouse connection created'))
                  .catch(() =>
                    toast('Failed to create warehouse connection', 'danger'),
                  ),
              title: 'Connect Flagsmith Warehouse',
            })
          }
        />
      </div>
    )
  }

  return (
    <div className='mt-4 col-md-12'>
      {connections.map((connection) => (
        <WarehouseConnectionCard
          key={connection.id}
          connection={connection}
          onDelete={() =>
            deleteConnection({ environmentId, id: connection.id })
              .unwrap()
              .then(() => toast('Warehouse connection removed'))
              .catch(() =>
                toast('Failed to remove warehouse connection', 'danger'),
              )
          }
        />
      ))}
    </div>
  )
}

WarehouseTab.displayName = 'WarehouseTab'
export default WarehouseTab
