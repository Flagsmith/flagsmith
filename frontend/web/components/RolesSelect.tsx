import React, { FC, useState } from 'react'
import InlineModal from './InlineModal'
import { Role } from 'common/types/responses'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
import Icon from './Icon'

export type RoleSelectType = {
  disabled?: boolean
  roles: Role[] | undefined
  value: number[] | undefined
  isOpen?: boolean
  isRoleApiKey?: boolean
  onAdd: (id: number, isUser?: boolean) => void
  onRemove: (id: number, isUser?: boolean) => void
  onToggle: () => void
}
const RoleSelect: FC<RoleSelectType> = ({
  disabled,
  isOpen,
  isRoleApiKey,
  onAdd,
  onRemove,
  onToggle,
  roles,
  value,
}) => {
  const [filter, setFilter] = useState<string>('')
  const rolelist =
    roles &&
    roles.filter((v) => {
      const search = filter.toLowerCase()
      if (!search) return true
      return `${v.name}`.toLowerCase().includes(search)
    })

  return (
    <InlineModal
      title='Roles'
      isOpen={isOpen}
      onClose={onToggle}
      className='inline-modal--sm'
    >
      <Input
        disabled={disabled}
        value={filter}
        onChange={(e: InputEvent) => setFilter(Utils.safeParseEventValue(e))}
        className='full-width mb-2'
        placeholder='Type or choose a Role'
        search
      />
      <div style={{ maxHeight: 200, overflowY: 'auto' }}>
        {rolelist &&
          rolelist.map((v) => (
            <div className='assignees-list-item clickable' key={v.id}>
              <Row
                onClick={() => {
                  const isRemove = value?.includes(v.id)
                  if (isRemove && onRemove) {
                    onRemove(v.id)
                  } else if (!isRemove && onAdd) {
                    onAdd((isRoleApiKey ? v : v.id) as number)
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

export default RoleSelect
