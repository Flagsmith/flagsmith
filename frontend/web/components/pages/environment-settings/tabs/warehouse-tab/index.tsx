import { FC } from 'react'
import {
  useCreateWarehouseConnectionMutation,
  useDeleteWarehouseConnectionMutation,
  useGetWarehouseConnectionsQuery,
} from 'common/services/useWarehouseConnection'
import Button from 'components/base/forms/Button'
import Setting from 'components/Setting'
import WarehouseConnectionCard from './WarehouseConnectionCard'
import CreateWarehouseConnectionModal from './CreateWarehouseConnectionModal'

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

  const hasFlagsmithConnection = connections?.some(
    (c) => c.warehouse_type === 'flagsmith',
  )

  const handleOpenDrawer = () => {
    openModal(
      'Connect Warehouse',
      <CreateWarehouseConnectionModal
        save={(data) => createConnection({ environmentId, ...data }).unwrap()}
      />,
      'side-modal side-modal--narrow',
    )
  }

  return (
    <div className='mt-4 col-md-12'>
      <div className='d-flex justify-content-end mb-3'>
        <Button onClick={handleOpenDrawer} size='small'>
          Connect your private warehouse
        </Button>
      </div>
      {!hasFlagsmithConnection && (
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
      )}
      {connections?.map((connection) => (
        <WarehouseConnectionCard
          key={connection.uuid}
          connection={connection}
          onDelete={() =>
            deleteConnection({ environmentId, uuid: connection.uuid })
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
