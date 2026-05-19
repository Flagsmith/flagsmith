import React, { FC, useState } from 'react'
import {
  WarehouseConnection,
  WarehouseConnectionStatus,
} from 'common/types/responses'
import ColorSwatch from 'components/ColorSwatch'
import Tooltip from 'components/Tooltip'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import WarehouseEventCodeHelp from './WarehouseEventCodeHelp'
import WarehouseStats from './WarehouseStats'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'

type WarehouseConnectionCardProps = {
  connection: WarehouseConnection
  onDelete: () => void
}

const STATUS_COLOUR: Record<WarehouseConnectionStatus, string> = {
  connected: '#27AE60',
  errored: '#EB5757',
  pending_connection: '#F2C94C',
}

const STATUS_LABEL: Record<WarehouseConnectionStatus, string> = {
  connected: 'Connected',
  errored: 'Errored',
  pending_connection: 'Pending Connection',
}

const WarehouseConnectionCard: FC<WarehouseConnectionCardProps> = ({
  connection,
  onDelete,
}) => {
  const [open, setOpen] = useState(false)
  const { contentRef, style: collapsibleStyle } = useCollapsibleHeight(open)

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    openConfirm({
      body: 'Are you sure you want to remove this warehouse connection?',
      onYes: onDelete,
      title: 'Remove Warehouse Connection',
    })
  }

  return (
    <div className='d-flex flex-column px-3 py-3 accordion-card m-0'>
      <div
        className='d-flex flex-row align-items-center justify-content-between'
        style={{ cursor: 'pointer' }}
        onClick={() => setOpen(!open)}
      >
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
        <div className='d-flex flex-row align-items-center gap-2'>
          <button
            type='button'
            className='btn btn-with-icon'
            onClick={handleDelete}
          >
            <Icon name='trash-2' width={20} fill='#656D7B' />
          </button>
          <span className='p-1' aria-label={open ? 'Collapse' : 'Expand'}>
            <Icon name={open ? 'chevron-up' : 'chevron-down'} width={16} />
          </span>
        </div>
      </div>
      <div ref={contentRef} style={collapsibleStyle}>
        <div className='mt-3 mb-2 d-flex flex-column gap-3'>
          {connection.status === 'pending_connection' ? (
            <>
              <WarehouseEventCodeHelp />
              <Button className='align-self-end' theme='primary'>
                Send your first event
              </Button>
            </>
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
    </div>
  )
}

WarehouseConnectionCard.displayName = 'WarehouseConnectionCard'
export default WarehouseConnectionCard
