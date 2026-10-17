import React, { FC } from 'react'
import IconButton from 'components/base/IconButton'
import cn from 'classnames'
import Icon from 'components/icons/Icon'
import Token from 'components/Token'
import Utils from 'common/utils/utils'

type ServerSideKeyRowProps = {
  id: string
  keyValue: string
  name: string
  isDeleting: boolean
  onRemove: (id: string, name: string) => void
}

const ServerSideKeyRow: FC<ServerSideKeyRowProps> = ({
  id,
  isDeleting,
  keyValue,
  name,
  onRemove,
}) => {
  return (
    <Row
      className={cn('list-item', {
        'opacity-50 pointer-events-none': isDeleting,
      })}
    >
      <Flex className='table-column px-3 font-weight-medium'>{name}</Flex>
      <div className='table-column'>
        <Token style={{ width: 280 }} token={keyValue} />
      </div>
      <IconButton
        variant='ghost'
        size='medium'
        aria-label={`Copy key ${name}`}
        onClick={() => {
          Utils.copyToClipboard(keyValue)
        }}
        className='ms-2'
      >
        <Icon width={20} name='copy' />
      </IconButton>
      <div className='table-column'>
        <IconButton
          variant='ghost'
          size='medium'
          aria-label={`Delete key ${name}`}
          onClick={() => onRemove(id, name)}
          id='remove-sdk-key'
        >
          <Icon width={20} name='trash-2' />
        </IconButton>
      </div>
    </Row>
  )
}

export default ServerSideKeyRow
