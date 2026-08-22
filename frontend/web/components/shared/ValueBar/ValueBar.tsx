import { FC } from 'react'
import cn from 'classnames'
import './ValueBar.scss'

export type ValueBarProps = {
  /** 0 to 100. Callers clamp before passing. */
  percent: number
  /** Any CSS colour. Passed inline because the width beside it must be. */
  colour: string
  /** Sizes the track in its row, e.g. `flex-1`. */
  className?: string
  /**
   * Meter semantics. Omitted when the bar compares values against each other
   * rather than measuring one against an allowance, since there is then no
   * maximum to report.
   */
  ariaLabel?: string
  ariaValueNow?: number
  ariaValueText?: string
}

/**
 * A track with a proportional fill, carrying no semantics of its own: usage
 * against a plan is a meter, a breakdown row is a comparison with no maximum,
 * and only the caller knows which it is drawing.
 *
 * `meter` rather than `progressbar`, because nothing here is a task advancing.
 * ARIA reserves progressbar for that and meter for a value inside a known
 * range, which is what a plan allowance is.
 */
const ValueBar: FC<ValueBarProps> = ({
  ariaLabel,
  ariaValueNow,
  ariaValueText,
  className,
  colour,
  percent,
}) => {
  const isMeter = ariaValueNow !== undefined

  return (
    <div
      className={cn(
        'value-bar rounded-full overflow-hidden bg-surface-muted',
        className,
      )}
      role={isMeter ? 'meter' : undefined}
      aria-label={ariaLabel}
      aria-valuenow={ariaValueNow}
      aria-valuemin={isMeter ? 0 : undefined}
      aria-valuemax={isMeter ? 100 : undefined}
      aria-valuetext={ariaValueText}
    >
      <div
        className='value-bar__fill h-100 rounded-full'
        style={{ background: colour, width: `${percent}%` }}
      />
    </div>
  )
}

export default ValueBar
