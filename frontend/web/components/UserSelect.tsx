import React, { useState } from 'react'
import InlineModal from './InlineModal'
import Icon from './Icon'
import classNames from 'classnames'
import Input from './base/forms/Input'
import Utils from 'common/utils/utils'
interface UserSelectProps {
  users: any[]
  value: any[]
  isOpen: boolean
  onToggle: () => void
  disabled: boolean
  onRemove?: (id: string) => void
  onAdd?: (id: string) => void
  onChange?: (value: any[]) => void
}

export const UserSelect: React.FC<UserSelectProps> = ({
  disabled,
  isOpen,
  onAdd,
  onChange,
  onRemove,
  onToggle,
  users,
  value,
}) => {
  const [filter, setFilter] = useState('')

  const matchingUsers = users?.filter((user) => {
    const search = filter?.toLowerCase()?.trim()

    if (!search) {
      return true
    }

    const fullName = `${user.first_name} ${user.last_name}`.toLowerCase()
    const email = user.email.toLowerCase()
    const splitTerms = search.split(/\s+/).filter(Boolean)

    return splitTerms.every(
      (term) => fullName.includes(term) || email.includes(term),
    )
  })

  const selectedValue = value || []
  const modalClassName = `inline-modal--sm`

  return (
    <InlineModal
      title='Assignees'
      isOpen={isOpen}
      onClose={onToggle}
      className={modalClassName}
    >
      <Input
        disabled={disabled}
        value={filter}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setFilter(Utils.safeParseEventValue(e))
        }
        className='full-width mb-2'
        placeholder='Search User'
        search
      />
      <div style={{ maxHeight: 200, overflowX: 'hidden', overflowY: 'auto' }}>
        {matchingUsers &&
          matchingUsers.map((v, i) => (
            <div
              onClick={() => {
                const isRemove = selectedValue.includes(v.id)
                if (isRemove && onRemove) {
                  onRemove(v.id)
                } else if (!isRemove && onAdd) {
                  onAdd(v.id)
                }
                onChange &&
                  onChange(
                    isRemove
                      ? selectedValue.filter((f) => f !== v.id)
                      : selectedValue.concat([v.id]),
                  )
              }}
              className='assignees-list-item clickable'
              key={v.id}
              data-test={`assignees-list-item-${i}`}
            >
              <Row
                className='flex-nowrap w-100 overflow-hidden overflow-ellipsis'
                space
              >
                <div
                  className={classNames(
                    selectedValue.includes(v.id) ? 'font-weight-bold' : '',
                    'overflow-ellipsis w-100',
                  )}
                >
                  {v.first_name} {v.last_name}
                  <div className='text-muted text-small'>{v.email}</div>
                </div>
                {selectedValue.includes(v.id) && (
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

export default UserSelect
