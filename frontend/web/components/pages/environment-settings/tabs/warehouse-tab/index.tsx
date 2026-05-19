import React, { FC } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
} from 'common/services/useWarehouseConnection'
import Setting from 'components/Setting'
import WarehouseConnectionCard from './WarehouseConnectionCard'

type WarehouseTabProps = {
  environmentId: string
}

const WarehouseTab: FC<WarehouseTabProps> = ({ environmentId }) => {
  const { data: connections, isLoading } = useGetWarehouseConnectionsQuery(
    { environmentId },
    { skip: !environmentId },
  )
  const [createConnection, { isLoading: isCreating }] =
    useCreateWarehouseConnectionMutation()
  const [deleteConnection] = useDeleteWarehouseConnectionMutation()

  const hasNoConnection =
    !isLoading && (!connections || connections.length === 0)

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

  if (!connections || connections.length === 0) {
    return null
  }

  return (
    <div className='mt-4 col-md-12'>
      {connections.map((connection) => (
        <WarehouseConnectionCard
          key={connection.uuid}
          connection={connection}
          onDelete={() =>
            deleteConnection({ environmentId })
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
