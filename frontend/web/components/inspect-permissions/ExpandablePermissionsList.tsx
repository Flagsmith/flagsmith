import React, { useState } from 'react'

import { PermissionLevel } from 'common/types/requests'

import Icon from 'components/Icon'
import Permissions from './Permissions'

type ExpandablePermissionsListProps<T> = {
  item: T
  level: PermissionLevel
  userId?: number
  projectId?: number
  getItemName: (item: T) => string
  getItemId: (item: T) => string | number
  getLevelId: (item: T) => string
  showSearch?: boolean
}

const ExpandablePermissionsList = <T,>({
  getItemId,
  getItemName,
  getLevelId,
  item,
  level,
  projectId,
  userId,
}: ExpandablePermissionsListProps<T>) => {
  const [expandedItems, setExpandedItems] = useState<(string | number)[]>([])

  const toggleExpand = async (id: string | number) => {
    setExpandedItems((prevExpanded) =>
      prevExpanded.includes(id)
        ? prevExpanded.filter((item) => item !== id)
        : [...prevExpanded, id],
    )
  }

  return (
    <div
      className='list-item d-flex flex-column justify-content-center py-2 list-item-sm'
      data-test={`permissions-${getItemName(item).toLowerCase()}`}
      key={getItemId(item)}
    >
      <Row
        className='px-3 flex-fill align-items-center user-select-none clickable'
        onClick={() => toggleExpand(getItemId(item))}
      >
        <Flex>
          <div className={'list-item-subtitle'}>
            <strong>{getItemName(item)}</strong>{' '}
          </div>
        </Flex>
        <div>
          <Icon
            fill={'#9DA4AE'}
            name={
              expandedItems.includes(getItemId(item))
                ? 'chevron-down'
                : 'chevron-right'
            }
          />
        </div>
      </Row>
      <div>
        {expandedItems.includes(getItemId(item)) && (
          <div className='modal-body px-3'>
            <Permissions
              level={level}
              levelId={getLevelId(item)}
              userId={userId}
              projectId={projectId}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export type { ExpandablePermissionsListProps }
export default ExpandablePermissionsList
