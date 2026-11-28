import { FC } from 'react'
import { percent } from './utils'

const Meter: FC<{ value: number; muted?: boolean; label: string }> = ({
  label,
  muted,
  value,
}) => (
  <div className='flag-bisect__meter' aria-label={`${label} ${percent(value)}`}>
    <div className='flag-bisect__meter-track'>
      <div
        className={`flag-bisect__meter-fill${
          muted ? ' flag-bisect__meter-fill--muted' : ''
        }`}
        style={{
          '--flag-bisect-fill': `${Math.min(100, Math.max(0, value * 100))}%`,
        }}
      />
    </div>
    <span className='flag-bisect__meter-value'>{percent(value)}</span>
  </div>
)

export default Meter
