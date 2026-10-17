import { FC } from 'react'
import Icon from './icons/Icon'
import IconButton, { IconButtonProps } from './base/IconButton'

type ActionButtonType = {
  onClick: () => void
  'data-test'?: string
  size?: IconButtonProps['size']
}

const ActionButton: FC<ActionButtonType> = ({
  onClick,
  size = 'small',
  ...rest
}) => {
  return (
    <IconButton
      variant='ghost'
      size={size}
      aria-label='More actions'
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
