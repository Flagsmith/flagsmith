import React from 'react'
import { Organisation } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'
import Payment from 'components/modals/payment'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import StatItem, { StatItemProps } from 'components/StatItem'
import Text from 'components/base/Text'

type BillingTabProps = {
  organisation: Organisation
}

type LimitItem = Pick<StatItemProps, 'icon' | 'label'> & { value: string }

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

  const limitItems: LimitItem[] = [
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
  ].filter((item): item is LimitItem => item !== undefined)

  return (
    <div className='mt-4'>
      <Row space className='plan p-4 mb-4 flex-wrap gap-4'>
        <div>
          <Row className='flex-wrap gap-4'>
            <div>
              <Row style={{ width: '230px' }}>
                <div className='plan-icon'>
                  <Icon name='layers' width={32} />
                </div>
                <div>
                  <p className='fs-small lh-sm mb-0'>Your plan</p>
                  <Text variant='h4' level={4} className='mb-0'>
                    {planName}
                  </Text>
                </div>
              </Row>
            </div>
            <div>
              <Row style={{ width: '230px' }}>
                <div className='plan-icon'>
                  <Text
                    variant='h4'
                    level={4}
                    className='mb-0 text-center'
                    style={{ width: '32px' }}
                  >
                    ID
                  </Text>
                </div>
                <div>
                  <p className='fs-small lh-sm mb-0'>Organisation ID</p>
                  <Text variant='h4' level={4} className='mb-0'>
                    {organisation.id}
                  </Text>
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
                    <Text variant='h6' level={6} className='mb-0'>
                      {chargebee_email}
                    </Text>
                  </div>
                </Row>
              </div>
            )}
          </Row>
        </div>
        <div className='align-self-center'>
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
          <Text variant='h5' level={5} className='mt-4 mb-3'>
            Subscription Limits
          </Text>
          <Row className='plan p-4 mb-4 flex-wrap gap-4'>
            {limitItems.map((item) => (
              <StatItem
                key={item.label}
                icon={item.icon}
                label={item.label}
                value={item.value}
              />
            ))}
          </Row>
        </>
      )}
      <Text variant='h5' level={5}>
        Manage Payment Plan
      </Text>
      <Payment
        organisation={organisation}
        isPaymentsEnabled={Utils.getFlagsmithHasFeature('payments_enabled')}
      />
    </div>
  )
}
