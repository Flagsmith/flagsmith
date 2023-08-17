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
        borderRadius: '10px',
        minHeight: '60px',
      }}
    >
      {mainItems.map((mainItem, index) => (
        <div key={index}>
          <Row
            key={index}
            onClick={() => toggleExpand(mainItem.id)}
            style={{
              backgroundColor: '#fafafb',
              border: '1px solid rgba(101, 109, 123, 0.16)',
              borderRadius: '10px',
              opacity: 1,
            }}
            className='clickable cursor-pointer list-item-sm px-3'
          >
            <Flex>
              <div className={'list-item-subtitle'}>{mainItem.name}</div>
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
                // hasPermissions={(hasPermissions) =>
                //   setHasPermissions(hasPermissions)
                // }
              />
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default CollapsibleNestedList
