import React, { useState } from 'react'
import InlineModal from './InlineModal'
import { UserGroup } from 'common/types/responses'

type SelectedGroups = {
  group: string
}
type GroupSelectType = {
  disabled: boolean
  groups: UserGroup
  isOpen: boolean
  onAdd: () => void
  onRemove: () => void
  onToggle: boolean
  selectedGroups: SelectedGroups[]
}

const GroupSelect: FC<GroupSelectType> = ({
  disabled,
  groups,
  isOpen,
  onAdd,
  onRemove,
  onToggle,
  selectedGroups,
}) => {
  const [filter, setFilter] = useState<string>('')
  const grouplist =
    groups &&
    groups.filter((v) => {
      const search = filter.toLowerCase()
      if (!search) return true
      return `${v.name}`.toLowerCase().includes(search)
    })
  return (
    <InlineModal
      title='Groups'
      isOpen={isOpen}
      onClose={onToggle}
      className='inline-modal--tags'
    >
      <Input
        disabled={disabled}
        value={filter}
        onChange={(e: InputEvent) => setFilter(Utils.safeParseEventValue(e))}
        className='full-width mb-2'
        placeholder='Type or choose a Group'
      />
      <div style={{ maxHeight: 200, overflowY: 'auto' }}>
        {grouplist &&
          grouplist.map((v) => (
            <div className='list-item clickable' key={v.id}>
              <Row
                onClick={() => {
                  const isRemove = selectedGroups.includes(v.id)
                  if (isRemove && onRemove) {
                    onRemove(v.id, false)
                  } else if (!isRemove && onAdd) {
                    onAdd(v.id, false)
                  }
                }}
                space
              >
                <Flex
                  className={
                    selectedGroups.includes(v.id) ? 'font-weight-bold' : ''
                  }
                >
                  {v.name}
                </Flex>
                {selectedGroups.includes(v.id) && (
                  <span
                    style={{ fontSize: 24 }}
                    className='ion `text-primary` ion-ios-checkmark'
                  />
                )}
              </Row>
            </div>
          ))}
      </div>
    </InlineModal>
  )
}

export default GroupSelect
