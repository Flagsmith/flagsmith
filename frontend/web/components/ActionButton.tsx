import { FC } from 'react'
import Icon from './icons/Icon'
import IconButton, { IconButtonProps } from './base/IconButton'

type ActionButtonType = {
  onClick: () => void
  isOpen: boolean
  'data-test'?: string
  size?: IconButtonProps['size']
}

const ActionButton: FC<ActionButtonType> = ({
  isOpen,
  onClick,
  size = 'medium',
  ...rest
}) => {
  return (
    <IconButton
      variant='secondary'
      size={size}
      aria-label='More actions'
      aria-haspopup='menu'
      aria-expanded={isOpen}
      data-test={rest['data-test']}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
    >
      <Icon name='more-vertical' width={16} />
    </IconButton>
  )
}

export default ActionButton
