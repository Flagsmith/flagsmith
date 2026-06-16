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
  onSendTestEvent: () => void
  isSendingTestEvent: boolean
  isLoadingStats?: boolean
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

const WarehouseConnectionCard: FC<WarehouseConnectionCardProps> = ({
  connection,
  isLoadingStats,
  isSendingTestEvent,
  onDelete,
  onEdit,
  onSendTestEvent,
}) => {
  const typeLabel =
    connection.warehouse_type !== 'flagsmith'
      ? TYPE_LABEL[connection.warehouse_type] ?? connection.warehouse_type
      : null

  const isFlagsmith = connection.warehouse_type === 'flagsmith'
  const isPending = connection.status === 'pending_connection'
  const isConnected = connection.status === 'connected'

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
        <div className='d-flex flex-column'>
          <div className='d-flex flex-row align-items-center gap-2'>
            <span className='font-weight-medium'>{connection.name}</span>
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
          {typeLabel && (
            <span className='fst-italic text-muted' style={{ fontSize: 13 }}>
              {typeLabel}
              {connection.config &&
                'account_identifier' in connection.config &&
                connection.config.account_identifier &&
                `: ${connection.config.account_identifier}`}
            </span>
          )}
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
      <hr className='my-4' />
      <WarehouseStats
        errored={connection.status === 'errored'}
        lastEventReceived='-'
        loading={isLoadingStats}
        totalEventsReceived={connection.total_events_received}
        uniqueEventsCount={connection.unique_events_count}
      />
      <hr className='my-4' />
      {connection.status === 'pending_connection' && (
        <div className='d-flex flex-row flex-nowrap align-items-center gap-2 text-muted mb-2'>
          <Icon name='info' width={14} fill='#656D7B' />
          <span>
            Your test event is on its way. It can take up to a few hours to
            process the first event.
          </span>
        </div>
      )}
      <WarehouseEventCodeHelp />
      <div className='d-flex justify-content-end mt-3'>
        {!isFlagsmith && (
          <Button theme='outline' size='small' disabled>
            Test connection
          </Button>
        )}
        {isFlagsmith && !isPending && !isConnected && (
          <Button
            theme='primary'
            size='small'
            onClick={onSendTestEvent}
            disabled={isSendingTestEvent}
          >
            {isSendingTestEvent ? 'Sending...' : 'Send your first event'}
          </Button>
        )}
      </div>
    </div>
  )
}

WarehouseConnectionCard.displayName = 'WarehouseConnectionCard'
export default WarehouseConnectionCard
