import React from 'react'
import { Organisation } from 'common/types/responses'
import Utils from 'common/utils/utils'
import Payment from 'components/modals/payment'
import { useGetSubscriptionMetadataQuery } from 'common/services/useSubscriptionMetadata'
import StatItem, { StatItemProps } from 'components/StatItem'

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

  const limitItems: LimitItem[] = (
    [
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
    ] as (LimitItem | undefined)[]
  ).filter((item): item is LimitItem => item !== undefined)

  return (
    <div className='mt-4'>
      <Row space className='mb-4 flex-wrap gap-3 align-items-stretch'>
        <Row className='flex-wrap gap-3 align-items-stretch flex-1'>
          <StatItem icon='layers' label='Your plan' value={planName} />
          <StatItem label='Organisation ID' value={String(organisation.id)} />
          {!!chargebee_email && (
            <StatItem
              label='Management email'
              value={chargebee_email}
              size='sm'
            />
          )}
        </Row>
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
          <h5 className='mt-4 mb-3'>Subscription Limits</h5>
          {/* StatItem carries its own card, so this row is layout only. */}
          <Row className='mb-4 flex-wrap gap-3 align-items-stretch'>
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
      <h5>Manage Payment Plan</h5>
      <Payment
        organisation={organisation}
        isPaymentsEnabled={Utils.getFlagsmithHasFeature('payments_enabled')}
      />
    </div>
  )
}
