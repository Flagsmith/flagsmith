import React, { useState } from 'react'
import Icon from 'components/Icon'
import { EditPermissionsModal } from 'components/EditPermissions'

type MainItem = {
  name: string
}

type CollapsibleNestedListProps = {
  mainItems: MainItem[]
  isButtonVisible: boolean
  selectProject: (project) => void
  role: Role
  level: string
  id: string
}

const CollapsibleNestedList: React.FC<CollapsibleNestedListProps> = ({
  isButtonVisible,
  level,
  mainItems,
  role,
  // selectProject,
}) => {
  const [expandedItems, setExpandedItems] = useState<string[]>([])
  const [hasPermissions, setHasPermissions] = useState<boolean>(false)

  const toggleExpand = (id: string) => {
    setExpandedItems((prevExpanded) =>
      prevExpanded.includes(id)
        ? prevExpanded.filter((item) => item !== id)
        : [...prevExpanded, id],
    )
  }

  return (
    <div
      style={{
        border: '1px solid rgba(101, 109, 123, 0.16)',
        minHeight: '60px',
      }}
    >
      {mainItems.map((mainItem, index) => (
        <div key={index}>
          <Row
            key={index}
            style={{
              backgroundColor: '#fafafb',
              border: '1px solid rgba(101, 109, 123, 0.16)',
              opacity: 1,
            }}
            className='list-item clickable cursor-pointer list-item-sm px-3'
          >
            <Flex onClick={() => toggleExpand(mainItem.id)}>
              <div
                className={
                  hasPermissions
                    ? 'list-item-subtitle font-weight-medium'
                    : 'list-item-subtitle'
                }
              >
                {mainItem.name}
              </div>
            </Flex>
            {isButtonVisible && (
              <Button
                theme='text'
                // onClick={selectProject?.(mainItem.id)}
                disabled={false}
                checked={true}
              >
                {'Go to environments'}
              </Button>
            )}
            <Icon
              name={
                expandedItems.includes(mainItem.id)
                  ? 'chevron-down'
                  : 'chevron-right'
              }
              width={25}
            />
          </Row>
          <div>
            {expandedItems.includes(mainItem.id) && (
              <EditPermissionsModal
                id={mainItem.id}
                level={level}
                role={role}
                hasPermissions={(hasPermissions) =>
                  setHasPermissions(hasPermissions)
                }
              />
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default CollapsibleNestedList
