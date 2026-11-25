import React, { FC } from 'react'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'

type ModalCloseType = {
  onClick: () => void
}

const ModalClose: FC<ModalCloseType> = ({ onClick }) => (
  <IconButton
    aria-label='Close'
    variant='ghost'
    size='medium'
    onClick={onClick}
  >
    <Icon name='close' width={20} />
  </IconButton>
)

export default ModalClose
