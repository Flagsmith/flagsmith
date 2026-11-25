import React, { useState } from 'react'
import Icon from 'components/icons/Icon'
import Constants from 'common/constants'
import { FeatureHealthEventReasonTextBlock } from 'common/types/responses'
import useCollapsibleHeight from 'common/hooks/useCollapsibleHeight'

interface EventTextBlocksProps {
  textBlocks: FeatureHealthEventReasonTextBlock[] | undefined
}

const CollapsibleText: React.FC<{
  collapsed: boolean
  children: React.ReactNode
}> = ({ children, collapsed }) => {
  const { contentRef, style } = useCollapsibleHeight(!collapsed)

  return (
    <div ref={contentRef} style={style}>
      {children}
    </div>
  )
}

const EventTextBlocks: React.FC<EventTextBlocksProps> = ({ textBlocks }) => {
  const initialValue =
    textBlocks?.map((_, index) => ({ collapsed: index !== 0, id: index })) ?? []
  const [collapsibleItems, setCollapsibleItems] =
    useState<{ id: number; collapsed: boolean }[]>(initialValue)

  const handleCollapse = (index: number) => {
    if (!collapsibleItems?.[index]) {
      return null
    }

    setCollapsibleItems((prev) => {
      const updatedItems = [...prev]
      updatedItems[index].collapsed = !updatedItems?.[index]?.collapsed
      return updatedItems
    })
  }

  const color = Constants.featureHealth.unhealthyColor

  if (!textBlocks?.length) {
    return <></>
  }

  return (
    <div className='d-flex flex-column m-0 gap-2 flex-1'>
      <strong className='text-default'>Incident Insights</strong>
      {textBlocks.map((textBlock, index) => (
        <div key={`${textBlock.text}-${index}`}>
          {textBlock.title && (
            <div className='mb-2 text-default'>
              <strong style={{ color }}>{textBlock.title ?? 'Event'}</strong>
              {!!textBlock.text && (
                <Icon
                  name={
                    collapsibleItems?.[index]?.collapsed
                      ? 'chevron-down'
                      : 'chevron-up'
                  }
                  width={14}
                  fill={color}
                  style={{ marginBottom: -2 }}
                  className='ms-1'
                  onClick={() => handleCollapse(index)}
                />
              )}
            </div>
          )}
          <CollapsibleText collapsed={!!collapsibleItems?.[index]?.collapsed}>
            {textBlock.text}
          </CollapsibleText>
        </div>
      ))}
    </div>
  )
}
export default EventTextBlocks
