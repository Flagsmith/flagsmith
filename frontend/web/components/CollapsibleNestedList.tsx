import React, { useState } from 'react'

type SubItem = {
  title: string
}

type MainItem = {
  title: string
  subItems: SubItem[]
}

type Props = {
  mainItems: MainItem[]
  isButtonVisible: boolean
}

const CollapsibleNestedList: React.FC<Props> = ({
  isButtonVisible,
  mainItems,
}) => {
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpand = (title: string) => {
    setExpandedItems((prevExpanded) =>
      prevExpanded.includes(title)
        ? prevExpanded.filter((item) => item !== title)
        : [...prevExpanded, title],
    )
  }

  return (
    <div>
      {mainItems.map((mainItem, index) => (
        <div>
          <Row
            key={index}
            style={{
              backgroundColor: '#fafafb',
              border: '1px solid rgba(101, 109, 123, 0.16)',
              opacity: 1,
            }}
            className='list-item clickable cursor-pointer list-item-sm px-3'
            onClick={() => toggleExpand(mainItem.title)}
          >
            <Flex>
              <div className='list-item-subtitle'>{mainItem.title}</div>
            </Flex>
            {isButtonVisible && (
              <Button
                theme='text'
                onClick={() => console.log('DEBUG go to env')}
                disabled={false}
                checked={true}
              >
                {'Go to environments'}
              </Button>
            )}
          </Row>
          <div>
            {expandedItems.includes(mainItem.title) && (
              <ul>
                {mainItem.subItems.map((subItem, subIndex) => (
                  <Row className='my-4'>
                    <Flex>
                      <div className='list-item-subtitle'>{subItem.title}</div>
                    </Flex>
                    <Switch
                      onChange={() => console.log('DEBUG swicht')}
                      disabled={false}
                      checked={true}
                    />
                  </Row>
                ))}
              </ul>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default CollapsibleNestedList
