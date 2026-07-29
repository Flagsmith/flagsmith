import React, { FC } from 'react'
import Button from './base/forms/Button'
import Flex from './base/grid/Flex'
import Icon from './icons/Icon'
import Input from './base/forms/Input'
import Row from './base/grid/Row'
import Utils from 'common/utils/utils'

// Minimal read-only input + icon-only Copy button pattern. The codebase has
// half a dozen consumers rolling this inline (CreateSAML's ACS URL, SDK
// keys, webhook URLs, etc.) — they should all migrate here in a follow-up.
// Keep the API tight for now to avoid pre-committing to choices that don't
// fit every existing consumer.
type CopyFieldProps = {
  value: string
  className?: string
  'data-test'?: string
}

const CopyField: FC<CopyFieldProps> = ({
  className,
  'data-test': dataTest,
  value,
}) => {
  const onCopy = () => Utils.copyToClipboard(value)

  return (
    <Row className='gap-2 align-items-center'>
      <Flex>
        <Input
          value={value}
          readOnly
          className={className}
          data-test={dataTest}
        />
      </Flex>
      <Button
        theme='secondary'
        className='btn-with-icon'
        onClick={onCopy}
        aria-label='Copy to clipboard'
      >
        <Icon name='copy' width={20} />
      </Button>
    </Row>
  )
}

export default CopyField
