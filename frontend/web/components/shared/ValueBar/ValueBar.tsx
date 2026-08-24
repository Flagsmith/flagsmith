import { FC } from 'react'
import cn from 'classnames'
import './ValueBar.scss'

export type ValueBarProps = {
  percent: number
  colour: string
  className?: string
  ariaLabel?: string
  ariaValueNow?: number
  ariaValueText?: string
}

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
