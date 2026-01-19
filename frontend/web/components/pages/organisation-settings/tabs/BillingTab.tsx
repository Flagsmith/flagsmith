import React, { FC } from 'react'
import { Organisation } from 'common/types/responses'
import Icon, { IconName } from 'components/Icon'
import Utils from 'common/utils/utils'
import Payment from 'components/modals/Payment'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'

type LimitItemProps = {
  icon: IconName
  label: string
  value: string
}

const LimitItem: FC<LimitItemProps> = ({ icon, label, value }) => (
  <Row>
    <div className='plan-icon'>
      <Icon name={icon} width={32} />
    </div>
    <div>
      <p className='fs-small lh-sm mb-0'>{label}</p>
      <h4 className='mb-0'>{value}</h4>
    </div>
  </Row>
)

type BillingTabProps = {
  organisation: Organisation
}

export const BillingTab = ({ organisation }: BillingTabProps) => {
  const { data: subscriptionMeta } = useGetSubscriptionMetadataQuery({
    id: organisation.id,
  })

  const {
    audit_log_visibility_days,
    chargebee_email,
    feature_history_visibility_days,
    max_api_calls,
    max_projects,
    max_seats,
  } = subscriptionMeta || {}
  const planName = Utils.getPlanName(organisation.subscription?.plan) || 'Free'

  const formatLimit = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'Unlimited'
    return Utils.numberWithCommas(value)
  }

  const formatDays = (value: number | null | undefined): string => {
    if (value === null || value === undefined) return 'Unlimited'
    if (value === 0) return 'Not available'
    return `${value} days`
  }

  const showAuditLog = audit_log_visibility_days !== 0
  const showFeatureHistory =
    Utils.getFlagsmithHasFeature('feature_versioning') &&
    feature_history_visibility_days !== 0

  const limitItems: LimitItemProps[] = [
    {
      icon: 'bar-chart',
      label: 'API Calls',
      value: formatLimit(max_api_calls),
    },
    { icon: 'people', label: 'Team Seats', value: formatLimit(max_seats) },
    { icon: 'layers', label: 'Projects', value: formatLimit(max_projects) },
    showAuditLog
      ? {
          icon: 'list',
          label: 'Audit Log',
          value: formatDays(audit_log_visibility_days),
        }
      : undefined,
    showFeatureHistory
      ? {
          icon: 'clock',
          label: 'Feature History',
          value: formatDays(feature_history_visibility_days),
        }
      : undefined,
  ].filter((item): item is LimitItemProps => item !== undefined)

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
      {subscriptionMeta && (
        <>
          <h5 className='mt-4 mb-3'>Subscription Limits</h5>
          <Row className='plan p-4 mb-4'>
            <Row className='flex-wrap gap-5'>
              {limitItems.map((item) => (
                <LimitItem
                  key={item.label}
                  icon={item.icon}
                  label={item.label}
                  value={item.value}
                />
              ))}
            </Row>
          </Row>
        </>
      )}
      <h5>Manage Payment Plan</h5>
      <Payment viewOnly={false} />
    </div>
  )
}
