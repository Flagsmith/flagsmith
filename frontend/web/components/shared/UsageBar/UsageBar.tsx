import { FC } from 'react'
import {
  colorBorderDanger,
  colorBorderWarning,
  colorSurfaceAction,
} from 'common/theme/tokens'
import Format from 'common/utils/format'
import ValueBar from 'components/shared/ValueBar'
import UsageBarThresholds from './UsageBarThresholds'
import { boundPercent, toneFor, usagePercent } from './utils'
import './UsageBar.scss'

const FILL_COLOURS = {
  danger: colorBorderDanger,
  success: colorSurfaceAction,
  warning: colorBorderWarning,
}

export type { UsageTone } from './utils'

export type UsageBarProps = {
  usage: number
  limit: number
  label?: string
  thresholds?: number[]
  warnAt?: number
  ariaLabel?: string
}

const UsageBar: FC<UsageBarProps> = ({
  ariaLabel,
  label,
  limit,
  thresholds,
  usage,
  warnAt = 85,
}) => {
  const percent = usagePercent(usage, limit)
  const boundedPercent = boundPercent(percent)
  const tone = toneFor(percent, warnAt)

  return (
    <div className='usage-bar mb-2'>
      {label && (
        <div className='d-flex justify-content-between align-items-center mb-1'>
          <span className='fs-small fw-normal'>{label}</span>
          <span className='fs-small fw-bold'>
            {usage}/{limit}
          </span>
        </div>
      )}

      <div
        className={
          thresholds?.length ? 'usage-bar__wrap position-relative' : undefined
        }
      >
        <ValueBar
          percent={boundedPercent}
          colour={FILL_COLOURS[tone]}
          ariaLabel={label ?? ariaLabel}
          ariaValueNow={boundedPercent}
          ariaValueText={`${percent}% of ${Format.shortenNumber(limit)}`}
        />

        {!!thresholds?.length && <UsageBarThresholds thresholds={thresholds} />}
      </div>
    </div>
  )
}

export default UsageBar
