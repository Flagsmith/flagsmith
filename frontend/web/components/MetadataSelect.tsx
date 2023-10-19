import React, { FC, useState } from 'react'
import InlineModal from './InlineModal'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import Icon from './Icon'

export type MetadataSelectType = {
  disabled: boolean
  contentType: number
  metadataList: [] | undefined
  value: number[] | undefined
  isOpen: boolean
  onAdd: (id: number, isUser: boolean) => void
  onRemove: (id: number, isUser: boolean) => void
  onToggle: () => void
}
const MetadataSelect: FC<MetadataSelectType> = ({
  disabled,
  isOpen,
  metadataList,
  onAdd,
  onRemove,
  onToggle,
  value,
}) => {
  const [filter, setFilter] = useState<string>('')

  return (
    <InlineModal
      title='Metadata'
      isOpen={isOpen}
      onClose={onToggle}
      className='inline-modal--tags'
    >
      <Input
        disabled={disabled}
        value={filter}
        onChange={(e: InputEvent) => setFilter(Utils.safeParseEventValue(e))}
        className='full-width mb-2'
        placeholder='Type or choose a Metadata'
      />
      <div style={{ maxHeight: 200, overflowY: 'auto' }}>
        {metadataList &&
          metadataList.map((v) => (
            <div className='assignees-list-item clickable' key={v.id}>
              <Row
                onClick={() => {
                  const isRemove = value?.includes(v.id)
                  if (isRemove && onRemove) {
                    onRemove(v.id, false)
                  } else if (!isRemove && onAdd) {
                    onAdd(v.id, false)
                  }
                }}
                space
              >
                <Flex
                  className={value?.includes(v.id) ? 'font-weight-bold' : ''}
                >
                  {v.name}
                </Flex>
                {value?.includes(v.id) && (
                  <span className='mr-1'>
                    <Icon name='checkmark' fill='#6837FC' />
                  </span>
                )}
              </Row>
            </div>
          ))}
      </div>
    </InlineModal>
  )
}

export default MetadataSelect
