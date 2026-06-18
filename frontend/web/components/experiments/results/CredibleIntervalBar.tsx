import { FC } from 'react'
import { Inference } from 'common/types/responses'
import './results.scss'

type CredibleIntervalBarProps = {
  inference: Inference
  colour: string
  domain: number
}

const pct = (v: number, domain: number): number =>
  Math.max(0, Math.min(100, ((v + domain) / (2 * domain)) * 100))

const CredibleIntervalBar: FC<CredibleIntervalBarProps> = ({
  colour,
  domain,
  inference,
}) => {
  const left = pct(inference.ci_low, domain)
  const right = pct(inference.ci_high, domain)
  const point = pct(inference.lift, domain)
  return (
    <div className='experiment-results__ci'>
      <div className='experiment-results__ci-zero' style={{ left: '50%' }} />
      <div
        className='experiment-results__ci-range'
        style={{
          background: colour,
          left: `${left}%`,
          width: `${right - left}%`,
        }}
      />
      <div
        className='experiment-results__ci-point'
        style={{ background: colour, left: `${point}%` }}
      />
    </div>
  )
}

export default CredibleIntervalBar
