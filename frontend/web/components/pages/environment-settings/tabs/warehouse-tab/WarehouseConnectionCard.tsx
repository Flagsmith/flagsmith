import React, { FC, useRef, useState } from 'react'
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
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'
import useOutsideClick from 'common/useOutsideClick'

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
  const [open, setOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const { contentRef, style: collapsibleStyle } = useCollapsibleHeight(open)

  useOutsideClick(menuRef as React.RefObject<HTMLElement>, () =>
    setMenuOpen(false),
  )

  const handleDelete = () => {
    setMenuOpen(false)
    openConfirm({
      body: 'Are you sure you want to remove this warehouse connection?',
      onYes: onDelete,
      title: 'Remove Warehouse Connection',
    })
  }

  const handleEdit = () => {
    setMenuOpen(false)
    onEdit?.()
  }

  const displayName =
    connection.warehouse_type === 'flagsmith'
      ? connection.name
      : `${connection.name} (${
          TYPE_LABEL[connection.warehouse_type] ?? connection.warehouse_type
        })`

  const renderBody = () => {
    if (isSetupStatus(connection.status)) {
      if (connection.warehouse_type === 'flagsmith') {
        return (
          <>
            <WarehouseEventCodeHelp />
            <Button className='align-self-end' theme='primary'>
              Send your first event
            </Button>
          </>
        )
      }
      return (
        <pre className='bg-dark text-white p-3 rounded'>
          {'SELECT * FROM users'}
        </pre>
      )
    }
    return (
      <WarehouseStats
        errored={connection.status === 'errored'}
        lastEventReceived='19 May 2026, 14:32'
        totalEventsReceived={1247}
        uniqueEventsCount={38}
      />
    )
  }

  return (
    <div className='d-flex flex-column px-3 py-3 accordion-card m-0 mb-2'>
      <div
        role='button'
        tabIndex={0}
        className='d-flex flex-row align-items-center justify-content-between btn--accordion-header'
        onClick={() => setOpen(!open)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setOpen(!open)
          }
        }}
        aria-expanded={open}
      >
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
          <div
            ref={menuRef}
            className='feature-action'
            style={{ position: 'relative' }}
          >
            <Button
              size='xSmall'
              className='btn btn-with-icon'
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation()
                setMenuOpen(!menuOpen)
              }}
            >
              <Icon name='more-vertical' width={16} fill='#656D7B' />
            </Button>
            {menuOpen && (
              <div
                className='feature-action__list placed-bottom'
                style={{ right: 0 }}
              >
                {onEdit && (
                  <div
                    className='feature-action__item'
                    onClick={(e) => {
                      e.stopPropagation()
                      handleEdit()
                    }}
                  >
                    <Icon name='edit' width={16} fill='#656D7B' />
                    <span>Edit</span>
                  </div>
                )}
                <div
                  className='feature-action__item'
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDelete()
                  }}
                >
                  <Icon name='trash-2' width={16} fill='#656D7B' />
                  <span>Delete</span>
                </div>
              </div>
            )}
          </div>
          <Icon name={open ? 'chevron-up' : 'chevron-down'} width={16} />
        </div>
      </div>
      <div ref={contentRef} style={collapsibleStyle}>
        <div className='mt-3 mb-2 d-flex flex-column gap-3'>{renderBody()}</div>
      </div>
    </div>
  )
}

WarehouseConnectionCard.displayName = 'WarehouseConnectionCard'
export default WarehouseConnectionCard
