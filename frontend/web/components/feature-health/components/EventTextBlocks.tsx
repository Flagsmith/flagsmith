import React, { useState } from 'react'
import Constants from 'common/constants'
import Collapse from '@material-ui/core/Collapse'
import { IonIcon } from '@ionic/react'
import { chevronDown, chevronUp } from 'ionicons/icons'
import { FeatureHealthEventReasonTextBlock } from 'common/types/responses'

interface EventTextBlocksProps {
  textBlocks: FeatureHealthEventReasonTextBlock[] | undefined
}

const EventTextBlocks: React.FC<EventTextBlocksProps> = ({ textBlocks }) => {
  // Index is used here only because the data is read only.
  // Backend sorts created_at in descending order.
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
      <strong className='text-body'>Incident Insights</strong>
      {textBlocks.map((textBlock, index) => (
        <div key={`${textBlock.text}-${index}`}>
          {textBlock.title && (
            <div className='mb-2 text-body'>
              <strong style={{ color }}>{textBlock.title ?? 'Event'}</strong>
              {!!textBlock.text && (
                <IonIcon
                  style={{ color, marginBottom: -2 }}
                  className='ms-1'
                  icon={
                    collapsibleItems?.[index]?.collapsed
                      ? chevronDown
                      : chevronUp
                  }
                  onClick={() => handleCollapse(index)}
                />
              )}
            </div>
          )}
          <Collapse key={index} in={!collapsibleItems?.[index]?.collapsed}>
            {textBlock.text}
          </Collapse>
        </div>
      ))}
    </div>
  )
}
export default EventTextBlocks
