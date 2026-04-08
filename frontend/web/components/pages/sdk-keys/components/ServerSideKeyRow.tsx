import React, { FC } from 'react'
import cn from 'classnames'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
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
      <Button
        onClick={() => {
          Utils.copyToClipboard(keyValue)
        }}
        className='ml-2 btn-with-icon text-body'
      >
        <Icon name='copy' width={20} />
      </Button>
      <div className='table-column'>
        <Button
          onClick={() => onRemove(id, name)}
          id='remove-sdk-key'
          className='btn btn-with-icon text-body'
        >
          <Icon name='trash-2' width={20} />
        </Button>
      </div>
    </Row>
  )
}

export default ServerSideKeyRow
