import { FC } from 'react'
import IconButton, { IconButtonProps } from './base/IconButton'
import { DotsIcon } from './icons'

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
      aria-expanded={isOpen}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
    >
      <DotsIcon width={16} />
    </IconButton>
  )
}

export default ActionButton
