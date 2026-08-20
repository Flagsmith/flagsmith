import { FC } from 'react'
import {
  colorBorderDanger,
  colorBorderWarning,
  colorSurfaceAction,
} from 'common/theme/tokens'
import Format from 'common/utils/format'
import UsageBarHeader from './UsageBarHeader'
import UsageBarThresholds from './UsageBarThresholds'
import { boundPercent, toneFor, usagePercent } from './utils'
import './UsageBar.scss'

// The border tokens hold the saturated status colours and stay the same in both
// themes. The text ones are darkened for contrast and read muddy as a fill; the
// surface ones are 8% tints and read as empty track.
const FILL_COLOURS = {
  danger: colorBorderDanger,
  success: colorSurfaceAction,
  warning: colorBorderWarning,
}

export type { UsageTone } from './utils'

export type UsageBarProps = {
  usage: number
  limit: number
  /** Renders a label and a usage/limit figure above the bar. */
  label?: string
  /** Percentages to mark on the bar, e.g. the thresholds usage is notified at. */
  thresholds?: number[]
  /** Percentage at which the bar turns amber. */
  warnAt?: number
  /** Needed when there is no label to name the bar. */
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
      {label && <UsageBarHeader label={label} usage={usage} limit={limit} />}

      <div
        className={
          thresholds?.length ? 'usage-bar__wrap position-relative' : undefined
        }
      >
        <div
          className='usage-bar__track rounded-full overflow-hidden bg-surface-muted'
          role='progressbar'
          aria-label={label ?? ariaLabel}
          aria-valuenow={boundedPercent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuetext={`${percent}% of ${Format.shortenNumber(limit)}`}
        >
          <div
            className='h-100 rounded-full'
            style={{
              background: FILL_COLOURS[tone],
              width: `${boundedPercent}%`,
            }}
          />
        </div>

        {!!thresholds?.length && <UsageBarThresholds thresholds={thresholds} />}
      </div>
    </div>
  )
}

export default UsageBar
