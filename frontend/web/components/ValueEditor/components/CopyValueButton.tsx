import React, { FC, useCallback } from 'react'

import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import copyToClipboard from 'common/utils/copyToClipboard'

interface CopyValueButtonProps {
  value: string
}

const CopyValueButton: FC<CopyValueButtonProps> = ({ value }) => {
  // copyToClipboard rethrows after toasting the failure, so swallow it here
  // rather than leaving an unhandled rejection.
  const copy = useCallback(() => {
    copyToClipboard(value).catch(() => undefined)
  }, [value])

  return (
    <BareButton
      className='value-editor__copy'
      aria-label='Copy value'
      onClick={copy}
    >
      <Icon name='copy-outlined' width={20} />
    </BareButton>
  )
}

export default CopyValueButton
