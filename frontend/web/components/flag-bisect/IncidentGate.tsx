import { FC, useState } from 'react'
import {
  useAbortFlagBisectIncidentMutation,
  useApproveFlagBisectEnvelopeMutation,
  useFlagBisectRemediationMutation,
} from 'common/services/useFlagBisect'
import { FlagBisectIncident } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import { culpritNames, errorDetail, pendingGate } from './utils'

const IncidentGate: FC<{
  environmentId: string
  incident: FlagBisectIncident
}> = ({ environmentId, incident }) => {
  const [canary, setCanary] = useState(incident.canary_percent)
  const [reason, setReason] = useState('')
  const [approve, approveState] = useApproveFlagBisectEnvelopeMutation()
  const [abort, abortState] = useAbortFlagBisectIncidentMutation()
  const [remediate, remediateState] = useFlagBisectRemediationMutation()
  const gate = pendingGate(incident.state)
  const args = { environmentId, incidentId: incident.id }
  const error = approveState.error || abortState.error || remediateState.error

  if (!gate) {
    const live = ['PROBING', 'CONFIRMING', 'INVESTIGATING'].includes(
      incident.state,
    )
    return (
      <div className='flag-bisect__panel'>
        <h5 className='mb-2'>Human decisions</h5>
        <p className='text-secondary mb-2'>
          {live
            ? 'The swarm is probing inside the approved envelope. You can stop it at any time.'
            : 'No decision is waiting.'}
        </p>
        {live && (
          <>
            <input
              className='form-control mb-2'
              placeholder='Reason for stopping'
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
            <Button
              theme='secondary'
              disabled={reason.trim().length < 5 || abortState.isLoading}
              onClick={() => abort({ ...args, body: { reason } })}
            >
              Stop and remove the canary
            </Button>
          </>
        )}
        {error && <p className='text-danger mt-2'>{errorDetail(error)}</p>}
      </div>
    )
  }

  return (
    <div className='flag-bisect__panel flag-bisect__panel--gate'>
      {gate === 'envelope' && (
        <>
          <h5 className='mb-2'>Approve the envelope</h5>
          <p className='text-secondary mb-3'>
            The swarm may revert any of {incident.suspects.length} change(s) for
            a canary of {canary}% of identities only, for up to{' '}
            {incident.max_rounds} rounds and {incident.max_minutes} minutes.
            Nothing has changed yet.
          </p>
          <label className='mb-1' htmlFor='flag-bisect-canary'>
            Canary size (% of identities)
          </label>
          <input
            id='flag-bisect-canary'
            className='form-control mb-3'
            type='number'
            min={1}
            max={20}
            value={canary}
            onChange={(e) => setCanary(Number(e.target.value))}
          />
          <div className='d-flex gap-2'>
            <Button
              disabled={approveState.isLoading || canary < 1 || canary > 20}
              onClick={() =>
                approve({ ...args, body: { canary_percent: canary } })
              }
            >
              Approve and start probing
            </Button>
            <Button
              theme='secondary'
              disabled={abortState.isLoading}
              onClick={() =>
                abort({ ...args, body: { reason: 'Declined the envelope' } })
              }
            >
              Decline
            </Button>
          </div>
        </>
      )}
      {gate === 'propose' && (
        <>
          <h5 className='mb-2'>Propose the remediation</h5>
          <p className='text-secondary mb-3'>
            Restore <strong>{culpritNames(incident).join(' + ')}</strong> for
            everyone in this environment. A different person must approve it.
          </p>
          <Button
            disabled={remediateState.isLoading}
            onClick={() => remediate({ ...args, action: 'propose' })}
          >
            Propose remediation
          </Button>
        </>
      )}
      {gate === 'approve' && (
        <>
          <h5 className='mb-2'>Second-person approval</h5>
          <p className='text-secondary mb-3'>
            Restores <strong>{culpritNames(incident).join(' + ')}</strong> for
            everyone and reads it back. The proposer cannot approve.
          </p>
          <Button
            theme='danger'
            disabled={remediateState.isLoading}
            onClick={() => remediate({ ...args, action: 'approve' })}
          >
            Approve and apply
          </Button>
        </>
      )}
      {error && <p className='text-danger mt-2'>{errorDetail(error)}</p>}
    </div>
  )
}

export default IncidentGate
