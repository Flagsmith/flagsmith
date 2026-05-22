import { FC } from 'react'
import {
  WarehouseConnection,
  WarehouseConnectionStatus,
  WarehouseType,
} from 'common/types/responses'
import ColorSwatch from 'components/ColorSwatch'
import Tooltip from 'components/Tooltip'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import WarehouseEventCodeHelp from './WarehouseEventCodeHelp'
import WarehouseStats from './WarehouseStats'

type WarehouseConnectionCardProps = {
  connection: WarehouseConnection
  onDelete: () => void
  onEdit?: () => void
}

const STATUS_COLOUR: Record<WarehouseConnectionStatus, string> = {
  connected: '#27AE60',
  created: '#F2C94C',
  errored: '#EB5757',
  pending_connection: '#F2C94C',
}

const STATUS_LABEL: Record<WarehouseConnectionStatus, string> = {
  connected: 'Connected',
  created: 'Created',
  errored: 'Errored',
  pending_connection: 'Pending Connection',
}

const TYPE_LABEL: Partial<Record<WarehouseType, string>> = {
  clickhouse: 'ClickHouse',
  snowflake: 'Snowflake',
}

const isSetupStatus = (status: WarehouseConnectionStatus) =>
  status === 'created' || status === 'pending_connection'

const WarehouseConnectionCard: FC<WarehouseConnectionCardProps> = ({
  connection,
  onDelete,
  onEdit,
}) => {
  const displayName =
    connection.warehouse_type === 'flagsmith'
      ? connection.name
      : `${connection.name} (${
          TYPE_LABEL[connection.warehouse_type] ?? connection.warehouse_type
        })`

  const handleDelete = () => {
    openConfirm({
      body: 'Are you sure you want to remove this warehouse connection?',
      onYes: onDelete,
      title: 'Remove Warehouse Connection',
    })
  }

  return (
    <div className='d-flex flex-column px-3 py-3 border rounded'>
      <div className='d-flex flex-row align-items-center justify-content-between'>
        <div className='d-flex flex-row align-items-center gap-2'>
          <span className='font-weight-medium'>{displayName}</span>
          <Tooltip
            title={
              <ColorSwatch
                color={STATUS_COLOUR[connection.status]}
                size='sm'
                shape='circle'
              />
            }
            place='top'
          >
            {STATUS_LABEL[connection.status]}
          </Tooltip>
        </div>
        <div className='d-flex flex-row align-items-center gap-2'>
          {onEdit && (
            <Button
              size='xSmall'
              className='btn btn-with-icon'
              onClick={onEdit}
            >
              <Icon name='edit' width={16} fill='#656D7B' />
            </Button>
          )}
          <Button
            size='xSmall'
            className='btn btn-with-icon'
            onClick={handleDelete}
          >
            <Icon name='trash-2' width={16} fill='#656D7B' />
          </Button>
        </div>
      </div>
      <div className='mt-3 d-flex flex-column gap-3'>
        {isSetupStatus(connection.status) ? (
          <WarehouseEventCodeHelp />
        ) : (
          <WarehouseStats
            errored={connection.status === 'errored'}
            lastEventReceived='19 May 2026, 14:32'
            totalEventsReceived={1247}
            uniqueEventsCount={38}
          />
        )}
      </div>
    </div>
  )
}

WarehouseConnectionCard.displayName = 'WarehouseConnectionCard'
export default WarehouseConnectionCard
