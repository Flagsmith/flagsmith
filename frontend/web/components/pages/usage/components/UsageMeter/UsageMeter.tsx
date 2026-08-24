import { FC, ReactNode } from 'react'
import Format from 'common/utils/format'
import UsageBar from 'components/shared/UsageBar'
import {
  PlanLimit,
  toneFor,
  usagePercent,
} from 'components/shared/UsageBar/utils'
import { meterCopy } from './utils'
import './UsageMeter.scss'

const WARN_AT = 75
const NOTIFICATION_THRESHOLDS = [WARN_AT, 100]

export type UsageMeterProps = {
  total: number
  limit: PlanLimit
  note?: ReactNode
}

const UsageMeter: FC<UsageMeterProps> = ({ limit, note, total }) => {
  const copy = meterCopy(total, limit)
  const tone = toneFor(usagePercent(total, limit), WARN_AT)

  return (
    <div className='p-4 mb-3 border border-default rounded-lg bg-surface-default'>
      <div className='d-flex align-items-end justify-content-between gap-3 mb-4'>
        <div>
          <p className='fs-caption text-secondary mb-1'>Plan usage</p>
          <div className='d-flex align-items-end gap-2'>
            <span className={`usage-meter__percent fw-bold lh-1 text-${tone}`}>
              {copy.headline}
            </span>
            <span className='fs-captionSmall text-secondary'>
              {copy.headlineCaption}
            </span>
          </div>
        </div>
        <div className='usage-meter__fraction text-end'>
          <div>
            <strong>{Format.shortenNumber(total)}</strong>
            {copy.fractionSuffix}
          </div>
          <div className='fs-captionSmall text-secondary'>
            {copy.fractionCaption}
          </div>
        </div>
      </div>

      {!!limit && (
        <UsageBar
          usage={total}
          limit={limit}
          thresholds={NOTIFICATION_THRESHOLDS}
          warnAt={WARN_AT}
          ariaLabel='Plan usage'
        />
      )}

      {note}
    </div>
  )
}

export default UsageMeter
