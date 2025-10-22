import React, { useEffect, useMemo } from 'react'
import Icon from 'components/Icon'
import Constants from 'common/constants'
import { useDismissHealthEventMutation } from 'common/services/useHealthEvents'
import Button from 'components/base/forms/Button'
import moment from 'moment'
import { IonIcon } from '@ionic/react'
import { warning } from 'ionicons/icons'
import { HealthEvent } from 'common/types/responses'
import AppActions from 'common/dispatcher/app-actions'
import EventTextBlocks from './EventTextBlocks'
import EventURLBlocks from './EventUrlsBlock'

interface FeatureHealthEventsListProps {
  featureHealthEvents: HealthEvent[]
  projectId: number
  environmentId: number
  featureId: number
}

const FeatureHealthEventsList: React.FC<FeatureHealthEventsListProps> = ({
  environmentId,
  featureHealthEvents = [],
  featureId,
  projectId,
}) => {
  const unhealthyEvents = useMemo(
    () => featureHealthEvents?.filter((event) => event.type === 'UNHEALTHY'),
    [featureHealthEvents],
  )
  const [
    dismissHealthEvent,
    { error: dismissError, isLoading: isDismissing, isSuccess: isDismissed },
  ] = useDismissHealthEventMutation()

  useEffect(() => {
    if (isDismissed) {
      toast('Event dismissed')
      AppActions.refreshFeatures(projectId, environmentId)
    }
  }, [isDismissed, projectId, environmentId, featureId])

  useEffect(() => {
    if (dismissError) {
      toast('Failed to dismiss event', 'danger')
    }
  }, [dismissError])
  const handleDismiss = (eventId: number) => {
    dismissHealthEvent({ eventId, projectId })
  }
  return (
    <>
      <h5 className='mb-4'>Unhealthy Events</h5>
      <div className='d-flex flex-column gap-4'>
        {unhealthyEvents?.length === 0 && (
          <div className='text-center'>
            <p>No unhealthy events found</p>
          </div>
        )}
        {unhealthyEvents?.map((event) => (
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
                <div>
                  <Row>
                    <h6 className='mb-0'>{event.provider_name} Provider</h6>
                    <div className='ml-2'>
                      <Tooltip title={moment(event.created_at).fromNow()}>
                        {moment(event.created_at).format('Do MMM YYYY HH:mma')}
                      </Tooltip>
                    </div>
                  </Row>
                </div>
              </div>
              <Row>
                <Button
                  className='mr-1'
                  size='xSmall'
                  theme='secondary'
                  disabled={isDismissing}
                  onClick={() => handleDismiss(event.id)}
                >
                  {isDismissing ? 'Dismissing' : 'Dismiss'}
                </Button>
                <Tooltip title={<Icon width={18} name='info-outlined' />}>
                  When dismissed, this event will no longer be shown in the
                  Unhealthy Events list.
                </Tooltip>
              </Row>
            </div>
            <div className='d-flex' style={{ gap: 96 }}>
              <EventTextBlocks textBlocks={event?.reason?.text_blocks} />
              <EventURLBlocks urlBlocks={event?.reason?.url_blocks} />
            </div>
          </div>
        ))}
      </div>
    </>
  )
}

export default FeatureHealthEventsList
