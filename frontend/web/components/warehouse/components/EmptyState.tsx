import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import './EmptyState.scss'

type EmptyStateProps = {
  onConnect: () => void
}

const EmptyState: FC<EmptyStateProps> = ({ onConnect }) => {
  return (
    <div className='wh-empty-state'>
      <Icon name='layers' width={48} />
      <h2 className='wh-empty-state__heading'>No warehouse connected</h2>
      <p className='wh-empty-state__text'>
        Stream flag evaluation and custom event data to your data warehouse for
        experimentation and analysis.
      </p>
      <Button theme='primary' onClick={onConnect} iconLeft='plus' iconSize={16}>
        Connect Data Warehouse
      </Button>
    </div>
  )
}

EmptyState.displayName = 'WarehouseEmptyState'
export default EmptyState
