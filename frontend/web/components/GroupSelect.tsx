import React, { FC, useState } from 'react'
import InlineModal from './InlineModal'
import { UserGroup, UserGroupSummary } from 'common/types/responses'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import Icon from './Icon'

export type GroupSelectType = {
  disabled?: boolean
  groups: UserGroup[] | UserGroupSummary[] | undefined
  value: number[] | undefined
  isOpen: boolean
  size: string
  onAdd: (id: number, isUser: boolean) => void
  onRemove: (id: number, isUser: boolean) => void
  onToggle: () => void
}
const GroupSelect: FC<GroupSelectType> = ({
  disabled,
  groups,
  isOpen,
  onAdd,
  onRemove,
  onToggle,
  size,
  value,
}) => {
  const [filter, setFilter] = useState<string>('')
  const grouplist =
    groups &&
    groups.filter((v) => {
      const search = filter.toLowerCase()
      if (!search) return true
      return `${v.name}`.toLowerCase().includes(search)
    })
  const modalClassName = `inline-modal--tags${size}`
  return (
    <InlineModal
      title='Groups'
      isOpen={isOpen}
      onClose={onToggle}
      className={modalClassName}
    >
      <Input
        disabled={disabled}
        value={filter}
        onChange={(e: InputEvent) => setFilter(Utils.safeParseEventValue(e))}
        className='full-width mb-2'
        placeholder='Type or choose a Group'
        search
      />
      <div style={{ maxHeight: 200, overflowY: 'auto' }}>
        {grouplist &&
          grouplist.map((v) => (
            <div
              onClick={() => {
                const isRemove = value?.includes(v.id)
                if (isRemove && onRemove) {
                  onRemove(v.id, false)
                } else if (!isRemove && onAdd) {
                  onAdd(v.id, false)
                }
              }}
              className='assignees-list-item clickable'
              key={v.id}
            >
              <Row space>
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

export default GroupSelect
