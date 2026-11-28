import { FC, useState } from 'react'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetFlagBisectIncidentsQuery } from 'common/services/useFlagBisect'
import PageTitle from 'components/PageTitle'
import IncidentDetail from 'components/flag-bisect/IncidentDetail'
import SignalSourcePanel from 'components/flag-bisect/SignalSourcePanel'
import StateBadge from 'components/flag-bisect/StateBadge'
import './FlagBisectPage.scss'

const POLL_MS = 5000

const FlagBisectPage: FC = () => {
  const { environmentId } = useRouteContext()
  const { data, error, isLoading } = useGetFlagBisectIncidentsQuery(
    { environmentId: environmentId ?? '' },
    { pollingInterval: POLL_MS, skip: !environmentId },
  )
  const [selected, setSelected] = useState<number | null>(null)
  const incidents = data?.results ?? []
  const current = selected ?? incidents[0]?.id ?? null

  const content = () => {
    if (error) {
      return (
        <div className='flag-bisect__panel'>
          <h5 className='mb-2'>Flag Bisect is not available here</h5>
          <p className='text-secondary mb-0'>
            It is off unless the instance sets{' '}
            <code>FLAG_BISECT_ENABLED=true</code>, and it is limited to
            environment admins.
          </p>
        </div>
      )
    }
    if (isLoading) {
      return <p className='text-secondary'>Loading incidents…</p>
    }
    if (incidents.length === 0) {
      return (
        <div className='flag-bisect__panel'>
          <h5 className='mb-2'>No incidents</h5>
          <p className='text-secondary mb-0'>
            An incident opens when the failure rate your servers report to{' '}
            <code>/api/v1/flag-bisect/signals/</code> shifts.
          </p>
        </div>
      )
    }
    return (
      <>
        <div className='flag-bisect__tabs' role='tablist'>
          {incidents.map((i) => (
            <button
              key={i.id}
              role='tab'
              aria-selected={i.id === current}
              className='flag-bisect__tab'
              onClick={() => setSelected(i.id)}
            >
              #{i.id} <StateBadge state={i.state} />
            </button>
          ))}
        </div>
        {current !== null && environmentId && (
          <IncidentDetail environmentId={environmentId} incidentId={current} />
        )}
      </>
    )
  }

  return (
    <div className='app-container container flag-bisect'>
      <PageTitle title='Flag Bisect'>
        Find which recent flag change caused a regression, without rolling back
        all of them.
      </PageTitle>
      {!error && environmentId && (
        <SignalSourcePanel environmentId={environmentId} />
      )}
      {content()}
    </div>
  )
}

export default FlagBisectPage
