import React, { FC } from 'react'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'

type FeatureModalTitleProps = {
  name: string
  label: string
}

const FeatureModalTitle: FC<FeatureModalTitleProps> = ({ label, name }) => (
  <>
    <span className='text-truncate'>
      {/* Phones show just the name so the copy button stays beside it */}
      <span className='d-none d-md-inline'>{label}: </span>
      {name}
    </span>
    <IconButton
      variant='ghost'
      size='small'
      aria-label='Copy feature name'
      onClick={() => {
        Utils.copyToClipboard(name)
      }}
      className='ms-2'
    >
      <Icon width={16} name='copy' />
    </IconButton>
  </>
)

export default FeatureModalTitle
