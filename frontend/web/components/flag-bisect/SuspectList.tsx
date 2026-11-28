import { FC } from 'react'
import { FlagBisectIncident } from 'common/types/responses'
import Meter from './Meter'
import { culpritNames, describeChange } from './utils'

const SuspectList: FC<{ incident: FlagBisectIncident }> = ({ incident }) => {
  const culprits = culpritNames(incident)
  const suspects = [...incident.suspects].sort(
    (a, b) => b.posterior - a.posterior,
  )
  return (
    <div className='flag-bisect__panel'>
      <h5 className='mb-3'>Suspects</h5>
      {suspects.map((s) => (
        <div
          key={s.id}
          className={`flag-bisect__suspect${
            culprits.includes(s.feature_name)
              ? ' flag-bisect__suspect--culprit'
              : ''
          }`}
        >
          <div className='flag-bisect__suspect-head'>
            <code>{s.feature_name}</code>
            <span className='text-secondary'>{describeChange(s)}</span>
          </div>
          <div className='flag-bisect__suspect-odds'>
            <span className='text-secondary'>prior</span>
            <Meter label='prior' value={s.prior} muted />
            <span className='text-secondary'>now</span>
            <Meter label='posterior' value={s.posterior} />
          </div>
        </div>
      ))}
    </div>
  )
}

export default SuspectList
