import React, { FC } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionQuery,
} from 'common/services/useWarehouseConnection'
import Setting from './Setting'
import WarehouseConnectionCard from './WarehouseConnectionCard'

type WarehouseTabProps = {
  environmentId: string
}

const WarehouseTab: FC<WarehouseTabProps> = ({ environmentId }) => {
  const {
    data: connection,
    error,
    isLoading,
  } = useGetWarehouseConnectionQuery(
    { environmentId },
    { skip: !environmentId },
  )
  const [createConnection, { isLoading: isCreating }] =
    useCreateWarehouseConnectionMutation()
  const [deleteConnection] = useDeleteWarehouseConnectionMutation()

  const hasNoConnection =
    !connection && !isLoading && (error as { status?: number })?.status === 404

  if (hasNoConnection || (!connection && !isLoading)) {
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

  if (!connection) {
    return null
  }

  return (
    <div className='mt-4 col-md-12'>
      <WarehouseConnectionCard
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
    </div>
  )
}

WarehouseTab.displayName = 'WarehouseTab'
export default WarehouseTab
