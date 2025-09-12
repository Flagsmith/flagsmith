import { FC } from 'react'
import classNames from 'classnames'
import Icon from './Icon'
import Button, { ButtonType } from './base/forms/Button'

type ActionButtonType = {
  onClick: () => void
  'data-test'?: string
  size?: ButtonType['size']
}

const ActionButton: FC<ActionButtonType> = ({
  onClick,
  size = 'xSmall',
  ...rest
}) => {
  return (
    <Button
      size={size}
      className={classNames('btn btn-with-icon')}
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
