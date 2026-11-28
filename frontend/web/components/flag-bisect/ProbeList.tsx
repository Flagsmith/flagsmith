import { FC } from 'react'
import { FlagBisectIncident } from 'common/types/responses'

const ProbeList: FC<{ incident: FlagBisectIncident }> = ({ incident }) => (
  <div className='flag-bisect__panel'>
    <h5 className='mb-3'>Probes</h5>
    {incident.probes.length === 0 && (
      <p className='text-secondary'>
        No probes yet. Each needs the approved envelope.
      </p>
    )}
    <ol className='flag-bisect__probes'>
      {incident.probes.map((p) => (
        <li
          key={p.round}
          className={`flag-bisect__probe flag-bisect__probe--${
            p.verdict || 'running'
          }`}
        >
          <div className='d-flex justify-content-between'>
            <strong>
              Round {p.round}
              {p.kind === 'CONFIRM' ? ' (confirmation)' : ''}
            </strong>
            <span>{p.verdict ? p.verdict.replace('_', ' ') : 'measuring'}</span>
          </div>
          <div className='text-secondary'>
            Reverted for the canary: {p.reverted_features.join(', ')}
          </div>
          <div className='text-secondary'>
            canary {p.canary_failures}/{p.canary_total} · everyone else{' '}
            {p.main_failures}/{p.main_total}
            {p.judgement
              ? ` · recovered ${Math.round(p.judgement.recovered * 100)}%`
              : ''}
          </div>
        </li>
      ))}
    </ol>
  </div>
)

export default ProbeList
