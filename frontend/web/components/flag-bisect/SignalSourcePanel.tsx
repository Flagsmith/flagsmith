import { FC, useEffect, useState } from 'react'
import {
  useDeleteFlagBisectSignalSourceMutation,
  useGetFlagBisectSignalSourceQuery,
  useUpdateFlagBisectSignalSourceMutation,
} from 'common/services/useFlagBisect'
import Button from 'components/base/forms/Button'
import { errorDetail } from './utils'

const SignalSourcePanel: FC<{ environmentId: string }> = ({
  environmentId,
}) => {
  const { data } = useGetFlagBisectSignalSourceQuery({ environmentId })
  const [save, saveState] = useUpdateFlagBisectSignalSourceMutation()
  const [remove, removeState] = useDeleteFlagBisectSignalSourceMutation()
  const [failure, setFailure] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    setFailure(data?.failure_event ?? '')
    setSuccess(data?.success_event ?? '')
  }, [data])

  if (!data) {
    return null
  }
  const configured = !!data.failure_event
  const error = saveState.error || removeState.error
  return (
    <div className='flag-bisect__panel mb-3'>
      <h5 className='mb-2'>Outcomes from Experimentation events</h5>
      <p className='text-secondary mb-2'>
        Count the events your app already sends to Flagsmith Experimentation:
        each failure event is a failed request and each success event a
        successful one, for the identity it was sent for.
      </p>
      {!data.events_stored_in_flagsmith && (
        <p className='text-secondary mb-2'>
          This environment does not store events in Flagsmith yet. Use the
          Flagsmith database as the warehouse for Experiments, or report
          outcomes to <code>/api/v1/flag-bisect/signals/</code>.
        </p>
      )}
      <div className='flag-bisect__source'>
        <label htmlFor='flag-bisect-failure'>
          Failure event
          <input
            id='flag-bisect-failure'
            className='form-control'
            placeholder='checkout_failed'
            value={failure}
            onChange={(e) => setFailure(e.target.value)}
          />
        </label>
        <label htmlFor='flag-bisect-success'>
          Success event
          <input
            id='flag-bisect-success'
            className='form-control'
            placeholder='checkout_completed'
            value={success}
            onChange={(e) => setSuccess(e.target.value)}
          />
        </label>
        <Button
          disabled={!failure.trim() || !success.trim() || saveState.isLoading}
          onClick={() =>
            save({
              body: { failure_event: failure, success_event: success },
              environmentId,
            })
          }
        >
          Save
        </Button>
        {configured && (
          <Button
            theme='secondary'
            disabled={removeState.isLoading}
            onClick={() => remove({ environmentId })}
          >
            Stop reading events
          </Button>
        )}
      </div>
      {error && <p className='text-danger mt-2 mb-0'>{errorDetail(error)}</p>}
    </div>
  )
}

export default SignalSourcePanel
