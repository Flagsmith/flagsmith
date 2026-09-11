import { FC } from 'react'
import Icon from 'components/icons/Icon'
import { CurrentBillingPeriod } from 'common/types/responses'
import { billingPeriodCopy } from 'components/pages/usage/billingPeriod'

export type BillingStripProps = {
  period: CurrentBillingPeriod | null | undefined
}

/** Renders nothing on a rolling window, which has no period to describe. */
const BillingStrip: FC<BillingStripProps> = ({ period }) => {
  const copy = billingPeriodCopy(period)

  if (!copy) {
    return null
  }

  return (
    <div className='d-flex align-items-center justify-content-between gap-3 flex-wrap px-3 py-2 mb-3 border border-default rounded-lg bg-surface-default'>
      <div className='d-flex align-items-center gap-2'>
        <span className='text-action d-flex'>
          <Icon name='calendar' width={18} />
        </span>
        <span className='fs-captionSmall text-secondary'>Billing period</span>
        <span className='fs-captionSmall fw-semibold'>{copy.range}</span>
      </div>
      <div className='d-flex align-items-center gap-2'>
        <span className='text-secondary d-flex'>
          <Icon name='refresh' width={14} />
        </span>
        <span className='fs-captionSmall'>{copy.resets}</span>
      </div>
    </div>
  )
}

export default BillingStrip
