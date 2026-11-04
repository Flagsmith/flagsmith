import React, { FC, useId } from 'react'
import IconButton from './base/IconButton'
import Flex from './base/grid/Flex'
import FieldLabel from './base/forms/FieldLabel'
import Icon from './icons/Icon'
import Input from './base/forms/Input'
import Row from './base/grid/Row'
import { TooltipProps } from './Tooltip'
import Utils from 'common/utils/utils'

// Read-only input + icon-only Copy button. Optionally renders a wired label
// (with tooltip) above the row — use `title` + `tooltip` for that, matching
// InputGroup's prop naming convention.
type CopyFieldProps = {
  value: string
  className?: string
  'data-test'?: string
  title?: string
  tooltip?: string
  tooltipPlace?: TooltipProps['place']
}

const CopyField: FC<CopyFieldProps> = ({
  className,
  'data-test': dataTest,
  title,
  tooltip,
  tooltipPlace,
  value,
}) => {
  const onCopy = () => Utils.copyToClipboard(value)
  const inputId = useId()

  const row = (
    <Row className='gap-2 align-items-center'>
      <Flex>
        <Input
          id={inputId}
          value={value}
          readOnly
          className={className}
          data-test={dataTest}
        />
      </Flex>
      <IconButton
        variant='secondary'
        size='large'
        onClick={onCopy}
        aria-label='Copy to clipboard'
      >
        <Icon width={20} name='copy' />
      </IconButton>
    </Row>
  )

  if (!title) return row

  return (
    <div>
      <FieldLabel
        htmlFor={inputId}
        tooltip={tooltip}
        tooltipPlace={tooltipPlace}
      >
        {title}
      </FieldLabel>
      {row}
    </div>
  )
}

export default CopyField
