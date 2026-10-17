import { FC } from 'react'
import Icon from './icons/Icon'
import IconButton, { IconButtonProps } from './base/IconButton'

type ActionButtonType = {
  onClick: () => void
  isOpen: boolean
  label: string
  size?: IconButtonProps['size']
}

const ActionButton: FC<ActionButtonType> = ({
  isOpen,
  label,
  onClick,
  size = 'medium',
}) => {
  return (
    <IconButton
      variant='secondary'
      size={size}
      aria-label={`More actions for ${label}`}
      aria-haspopup='menu'
      aria-expanded={isOpen}
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
