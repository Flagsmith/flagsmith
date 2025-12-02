import React from 'react'
import { Organisation } from 'common/types/responses'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'
import Payment from 'components/modals/Payment'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'

type BillingTabProps = {
  organisation: Organisation
}

export const BillingTab = ({ organisation }: BillingTabProps) => {
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery({
    id: String(organisation.id),
  })

  const { chargebee_email } = subscriptionMeta || {}
  const planName = Utils.getPlanName(organisation.subscription?.plan) || 'Free'

  return (
    <div className='mt-4'>
      <Row space className='plan p-4 mb-4'>
        <div>
          <Row>
            <div>
              <Row className='mr-3' style={{ width: '230px' }}>
                <div className='plan-icon'>
                  <Icon name='layers' width={32} />
                </div>
                <div>
                  <p className='fs-small lh-sm mb-0'>Your plan</p>
                  <h4 className='mb-0'>{planName}</h4>
                </div>
              </Row>
            </div>
            <div>
              <Row style={{ width: '230px' }} className='mr-3'>
                <div className='plan-icon'>
                  <h4 className='mb-0 text-center' style={{ width: '32px' }}>
                    ID
                  </h4>
                </div>
                <div>
                  <p className='fs-small lh-sm mb-0'>Organisation ID</p>
                  <h4 className='mb-0'>{organisation.id}</h4>
                </div>
              </Row>
            </div>
            {!!chargebee_email && (
              <div>
                <Row style={{ width: '230px' }}>
                  <div className='plan-icon'>
                    <Icon name='layers' width={32} />
                  </div>
                  <div>
                    <p className='fs-small lh-sm mb-0'>Management Email</p>
                    <h6 className='mb-0'>{chargebee_email}</h6>
                  </div>
                </Row>
              </div>
            )}
          </Row>
        </div>
        <div className='align-self-start'>
          {organisation.subscription?.subscription_id && (
            <Button
              theme='secondary'
              href='https://flagsmith.chargebeeportal.com/'
              target='_blank'
              className='btn'
            >
              Manage subscription
            </Button>
          )}
        </div>
      </Row>
      <h5>Manage Payment Plan</h5>
      <Payment viewOnly={false} />
    </div>
  )
}
