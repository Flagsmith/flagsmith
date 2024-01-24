import React, { FC, useState } from 'react'
import InlineModal from './InlineModal'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import Icon from './Icon'

export type MetadataSelectType = {
  disabled: boolean
  contentType: number
  metadata: [] | undefined
  value: number[] | undefined
  isOpen: boolean
  onAdd: (id: number) => void
  onRemove: (id: number) => void
  onToggle: () => void
}
const MetadataSelect: FC<MetadataSelectType> = ({
  disabled,
  isOpen,
  metadata,
  onAdd,
  onRemove,
  onToggle,
  value,
}) => {
  const [filter, setFilter] = useState<string>('')
  const metadataList =
    metadata &&
    metadata.filter((v) => {
      const search = filter.toLowerCase()
      if (!search) return true
      return `${v.name}`.toLowerCase().includes(search)
    })
  return (
    <InlineModal
      title='Metadata'
      isOpen={isOpen}
      onClose={onToggle}
      className='inline-modal--sm'
    >
      <Input
        disabled={disabled}
        value={filter}
        onChange={(e: InputEvent) => setFilter(Utils.safeParseEventValue(e))}
        className='full-width mb-2'
        placeholder='Type or choose a Metadata'
      />
      <div className='inline-modal__list'>
        {metadataList?.length
          ? metadataList.map((v) => (
              <div className='assignees-list-item clickable' key={v.id}>
                <Row
                  onClick={() => {
                    const isRemove = value?.includes(v.id)
                    if (isRemove && onRemove) {
                      onRemove(v.id)
                    } else if (!isRemove && onAdd) {
                      onAdd(v.id)
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
            ))
          : 'No metadata items'}
      </div>
    </InlineModal>
  )
}

export default MetadataSelect
