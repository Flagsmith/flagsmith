import React, { useState } from 'react'
import Icon from 'components/Icon'
import Constants from 'common/constants'
import { useGetHealthEventsQuery } from 'common/services/useHealthEvents'
import Button from 'components/base/forms/Button'
import moment from 'moment'
import Collapse from '@material-ui/core/Collapse'
import { IonIcon } from '@ionic/react'
import { chevronDown, chevronUp, warning } from 'ionicons/icons'
import {
  FeatureHealthEventReasonTextBlock,
  FeatureHealthEventReasonUrlBlock,
} from 'common/types/responses'

type FeatureHealthTabContentProps = {
  projectId: number
}

const EventTextBlocks = ({
  textBlocks,
}: {
  textBlocks: FeatureHealthEventReasonTextBlock[] | undefined
}) => {
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
    return null
  }

  return (
    <div className='d-flex flex-column m-0 gap-2 flex-1'>
      <strong className='text-body'>Incident Insights</strong>
      {textBlocks.map((textBlock, index) => (
        <div key={textBlock.text}>
          {textBlock.title && (
            <div className='mb-2 text-body'>
              <strong style={{ color }}>{textBlock.title ?? 'Event'}</strong>
              <IonIcon
                style={{ color, marginBottom: -2 }}
                className='ms-1'
                icon={
                  collapsibleItems?.[index]?.collapsed ? chevronDown : chevronUp
                }
                onClick={() => handleCollapse(index)}
              />
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

const EventURLBlocks = ({
  urlBlocks,
}: {
  urlBlocks: FeatureHealthEventReasonUrlBlock[] | undefined
}) => {
  if (!urlBlocks?.length) {
    return null
  }

  return (
    <div className='d-flex flex-column m-0 gap-2 align-items-start'>
      <div>
        <strong className='text-body'>Provider Links</strong>
      </div>
      {urlBlocks.map((urlBlock) => (
        <Button
          key={urlBlock.url}
          theme='text'
          onClick={() => window.open(urlBlock.url, '_blank')}
        >
          {urlBlock.title ?? 'Link'}{' '}
          <Icon name='open-external-link' width={14} fill='#6837fc' />
        </Button>
      ))}
    </div>
  )
}

const FeatureHealthTabContent: React.FC<FeatureHealthTabContentProps> = ({
  projectId,
}) => {
  const { data: healthEvents, isLoading } = useGetHealthEventsQuery(
    { projectId: String(projectId) },
    { skip: !projectId },
  )

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  return (
    <div>
      <h5 className='mb-4'>Unhealthy Events</h5>
      <div className='d-flex flex-column gap-4'>
        {healthEvents?.map((event) => (
          <div
            className='border-1 p-3'
            style={{
              borderRadius: 6,
            }}
            key={event.created_at}
          >
            <div className='d-flex justify-content-between align-items-center mb-4'>
              <div className='d-flex align-items-center'>
                <IonIcon
                  style={{
                    color: Constants.featureHealth.unhealthyColor,
                    marginBottom: -2,
                  }}
                  className='ms-1 mr-1'
                  icon={warning}
                />
                <h6 className='mb-0'>{event.provider_name} Provider</h6>
              </div>
              <div>
                <Tooltip title={moment(event.created_at).fromNow()}>
                  {moment(event.created_at).format('Do MMM YYYY HH:mma')}
                </Tooltip>
              </div>
            </div>
            <div className='d-flex' style={{ gap: 96 }}>
              <EventTextBlocks textBlocks={event?.reason?.text_blocks} />
              <EventURLBlocks urlBlocks={event?.reason?.url_blocks} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default FeatureHealthTabContent
