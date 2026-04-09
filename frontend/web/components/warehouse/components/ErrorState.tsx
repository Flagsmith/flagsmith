import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import ConnectionDetailsGrid from './ConnectionDetailsGrid'
import { ConnectionDetail, ConnectionError } from 'components/warehouse/types'
import './ErrorState.scss'

type ErrorStateProps = {
  error: ConnectionError
  details: ConnectionDetail[]
  onRetry: () => void
  onEdit: () => void
}

const ErrorState: FC<ErrorStateProps> = ({
  details,
  error,
  onEdit,
  onRetry,
}) => {
  return (
    <div className='wh-error'>
      {/* Error card */}
      <div className='wh-error__card'>
        <div className='wh-error__top'>
          <div className='wh-error__info'>
            <div className='wh-error__icon-box'>
              <Icon name='warning' width={24} />
            </div>
            <div className='wh-error__name-col'>
              <span className='wh-error__name'>Snowflake</span>
              <span className='wh-error__account'>
                myorg.snowflakecomputing.com
              </span>
            </div>
          </div>
          <span className='wh-error__badge'>
            <Icon name='warning' width={14} />
            Connection Failed
          </span>
        </div>

        <div className='wh-error__divider' />

        <div className='wh-error__message-box'>
          <div className='wh-error__message-header'>
            <span className='wh-error__message-label'>Last Error</span>
            <span className='wh-error__message-date'>{error.timestamp}</span>
          </div>
          <p className='wh-error__message-text'>{error.message}</p>
        </div>

        <div className='wh-error__divider' />

        <div className='wh-error__last-ok'>
          <span className='wh-error__last-ok-label'>
            Last successful delivery
          </span>
          <div className='wh-error__last-ok-value'>
            <span>{error.lastSuccessful}</span>
            <span className='wh-error__last-ok-date'>
              {error.lastSuccessfulDate}
            </span>
          </div>
        </div>
      </div>

      {/* Connection details */}
      <ConnectionDetailsGrid details={details} />

      {/* Actions */}
      <div className='wh-error__actions'>
        <Button theme='primary' size='small' onClick={onRetry}>
          Retry Connection
        </Button>
        <Button
          theme='outline'
          size='small'
          iconLeft='edit'
          iconSize={14}
          onClick={onEdit}
        >
          Edit Connection
        </Button>
      </div>
    </div>
  )
}

ErrorState.displayName = 'WarehouseErrorState'
export default ErrorState
