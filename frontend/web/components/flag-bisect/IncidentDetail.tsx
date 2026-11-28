import { FC, useEffect, useState } from 'react'
import { useGetFlagBisectIncidentQuery } from 'common/services/useFlagBisect'
import IncidentGate from './IncidentGate'
import Meter from './Meter'
import ProbeList from './ProbeList'
import SuspectList from './SuspectList'
import StateBadge from './StateBadge'
import {
  LIVE_STATES,
  culpritNames,
  headline,
  percent,
  stateTone,
} from './utils'

const POLL_MS = 5000

const IncidentDetail: FC<{ environmentId: string; incidentId: number }> = ({
  environmentId,
  incidentId,
}) => {
  const [poll, setPoll] = useState(POLL_MS)
  const { data: incident, isLoading } = useGetFlagBisectIncidentQuery(
    { environmentId, incidentId },
    { pollingInterval: poll },
  )
  useEffect(() => {
    if (incident) setPoll(LIVE_STATES.includes(incident.state) ? POLL_MS : 0)
  }, [incident])

  if (isLoading || !incident) {
    return <p className='text-secondary'>Loading the incident…</p>
  }
  const culprits = culpritNames(incident)
  return (
    <div className='flag-bisect__detail'>
      <div
        className={`flag-bisect__hero flag-bisect__hero--${stateTone(
          incident.state,
        )}`}
      >
        <div>
          <StateBadge state={incident.state} />
          <h3 className='mt-2 mb-1'>{headline(incident)}</h3>
          {incident.conclusion && culprits.length > 0 && (
            <span className='text-secondary'>
              {percent(incident.conclusion.confidence)}
              {incident.confirmed ? ', confirmed by a canary revert' : ''}
            </span>
          )}
        </div>
        <dl className='flag-bisect__stats'>
          <div>
            <dt>Onset</dt>
            <dd>{new Date(incident.onset_at).toLocaleTimeString()}</dd>
          </div>
          <div>
            <dt>Baseline</dt>
            <dd>{percent(incident.baseline_rate, 2)}</dd>
          </div>
          <div>
            <dt>During</dt>
            <dd>{percent(incident.regression_rate, 2)}</dd>
          </div>
          <div>
            <dt>Rounds</dt>
            <dd>
              {incident.rounds} / {incident.max_rounds}
            </dd>
          </div>
        </dl>
      </div>

      <div className='flag-bisect__grid'>
        <div className='flag-bisect__column'>
          <SuspectList incident={incident} />
          <ProbeList incident={incident} />
        </div>
        <div className='flag-bisect__column'>
          <IncidentGate environmentId={environmentId} incident={incident} />
          <div className='flag-bisect__panel'>
            <h5 className='mb-3'>Leading explanations</h5>
            {incident.hypotheses.map((h) => (
              <div
                className='flag-bisect__hypothesis'
                key={h.features.join('+')}
              >
                <span>
                  {h.features.length ? h.features.join(' + ') : 'none of these'}
                </span>
                <Meter label='probability' value={h.probability} />
              </div>
            ))}
          </div>
          <div className='flag-bisect__panel'>
            <h5 className='mb-3'>Swarm trail</h5>
            <p className='text-secondary fs-small mb-2'>Newest first</p>
            <ol className='flag-bisect__trail' reversed>
              {[...incident.messages].reverse().map((m, i) => (
                <li key={incident.messages.length - i}>
                  <span
                    className={`flag-bisect__agent flag-bisect__agent--${m.agent}`}
                  >
                    {m.agent}
                  </span>
                  <span>{m.text}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}

export default IncidentDetail
