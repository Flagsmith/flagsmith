import { FC } from 'react'
import classNames from 'classnames'
import Icon from './Icon'
import Button from './base/forms/Button'

type ActionButtonType = {
  onClick: () => void
  'data-test'?: string
}

const ActionButton: FC<ActionButtonType> = ({ onClick, ...rest }) => {
  return (
    <Button
      className={classNames('btn btn-with-icon btn-xs')}
      data-test={rest['data-test']}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
    >
      <div className='pointer-events-none'>
        <Icon name='more-vertical' width={16} fill='#656D7B' />
      </div>
    </Button>
  )
}

export default ActionButton
