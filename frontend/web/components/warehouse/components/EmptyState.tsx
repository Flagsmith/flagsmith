import React, { FC } from 'react'
import { motion } from 'motion/react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import { fadeIn } from 'common/utils/motion'
import './EmptyState.scss'

type EmptyStateProps = {
  onConnect: () => void
}

const EmptyState: FC<EmptyStateProps> = ({ onConnect }) => {
  return (
    <motion.div
      className='wh-empty-state'
      variants={fadeIn()}
      initial='hidden'
      animate='visible'
    >
      <Icon name='layers' width={48} />
      <h2 className='wh-empty-state__heading'>No warehouse connected</h2>
      <p className='wh-empty-state__text'>
        Stream flag evaluation and custom event data to your data warehouse for
        experimentation and analysis.
      </p>
      <Button theme='primary' onClick={onConnect} iconLeft='plus' iconSize={16}>
        Connect Data Warehouse
      </Button>
    </motion.div>
  )
}

EmptyState.displayName = 'WarehouseEmptyState'
export default EmptyState
