import { FC, useMemo, useState } from 'react'
import { useHistory } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import { useGetWarehouseConnectionsQuery } from 'common/services/useWarehouseConnection'
import { Experiment, ExperimentStatus } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import CreateExperimentWizard from 'components/experiments/CreateExperimentWizard'
import ExperimentsTable from 'components/experiments/ExperimentsTable'
import { IonIcon } from '@ionic/react'
import { addOutline, flaskOutline, settingsOutline } from 'ionicons/icons'
import 'components/experiments/ExperimentsListControls.scss'

type FilterTab = 'all' | ExperimentStatus

const TABS: { label: string; value: FilterTab }[] = [
  { label: 'All', value: 'all' },
  { label: 'Running', value: 'running' },
  { label: 'Created', value: 'created' },
  { label: 'Paused', value: 'paused' },
  { label: 'Completed', value: 'completed' },
]

const ExperimentsPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const [isCreating, setIsCreating] = useState(false)
  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [search, setSearch] = useState('')
  const history = useHistory()

  const { data: experiments, isLoading } = useGetExperimentsQuery(
    { environmentId: environmentId ?? '' },
    { skip: !environmentId },
  )

  const { data: warehouseConnections, isLoading: isLoadingWarehouse } =
    useGetWarehouseConnectionsQuery(
      { environmentId: environmentId ?? '' },
      { skip: !environmentId },
    )

  const hasWarehouse = (warehouseConnections?.length ?? 0) > 0

  const filtered = useMemo(() => {
    if (!experiments) return []
    let items: Experiment[] = experiments
    if (activeTab !== 'all') {
      items = items.filter((e) => e.status === activeTab)
    }
    if (search) {
      const lower = search.toLowerCase()
      items = items.filter(
        (e) =>
          e.name.toLowerCase().includes(lower) ||
          e.feature.name.toLowerCase().includes(lower),
      )
    }
    return items
  }, [experiments, activeTab, search])

  const counts = useMemo(() => {
    const c = { completed: 0, created: 0, paused: 0, running: 0 }
    experiments?.forEach((e) => {
      c[e.status]++
    })
    return c
  }, [experiments])

  if (!environmentId || !projectId) return null

  if (isCreating) {
    return (
      <div data-test='experiments-page' className='app-container container'>
        <PageTitle
          title='Create Experiment'
          cta={
            <Button theme='outline' onClick={() => setIsCreating(false)}>
              Cancel
            </Button>
          }
        />
        <CreateExperimentWizard
          environmentId={environmentId}
          projectId={projectId}
          onCreated={() => setIsCreating(false)}
        />
      </div>
    )
  }

  const experimentCount = experiments?.length ?? 0
  const settingsUrl = `/project/${projectId}/environment/${environmentId}/settings?tab=warehouse`

  const renderBody = () => {
    if (isLoading || isLoadingWarehouse) {
      return (
        <div className='text-center'>
          <Loader />
        </div>
      )
    }
    if (!hasWarehouse && experimentCount === 0) {
      return (
        <div className='text-center py-5'>
          <IonIcon
            icon={settingsOutline}
            style={{ fontSize: 48 }}
            className='text-muted mb-3 d-block mx-auto'
          />
          <h5>Data warehouse not configured</h5>
          <p className='text-muted mb-4'>
            Experiments require a data warehouse connection to collect and
            analyse results. Configure one in your environment settings to get
            started.
          </p>
          <Button onClick={() => history.push(settingsUrl)}>
            Configure Warehouse
          </Button>
        </div>
      )
    }
    if (experimentCount === 0) {
      return (
        <div className='text-center py-5'>
          <IonIcon
            icon={flaskOutline}
            style={{ fontSize: 48 }}
            className='text-muted mb-3 d-block mx-auto'
          />
          <h5>No experiments yet</h5>
          <p className='text-muted mb-4'>
            Create your first experiment to start testing hypotheses with your
            feature flags.
          </p>
          <Button onClick={() => setIsCreating(true)}>
            <IonIcon icon={addOutline} className='me-1' />
            Create Experiment
          </Button>
        </div>
      )
    }
    return (
      <>
        <div className='experiments-controls'>
          <div className='experiments-controls__tabs'>
            {TABS.map((tab) => (
              <button
                key={tab.value}
                type='button'
                className={`experiments-controls__tab ${
                  activeTab === tab.value
                    ? 'experiments-controls__tab--active'
                    : ''
                }`}
                onClick={() => setActiveTab(tab.value)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className='experiments-controls__search'>
            <Input
              value={search}
              onChange={(e: InputEvent) =>
                setSearch(Utils.safeParseEventValue(e))
              }
              placeholder='Search experiments...'
              search
              size='small'
            />
          </div>
        </div>
        {filtered.length > 0 ? (
          <ExperimentsTable
            experiments={filtered}
            environmentId={environmentId}
          />
        ) : (
          <div className='text-center py-5'>
            <p className='text-muted'>
              No experiments match your {search ? 'search' : 'filter'}.
            </p>
          </div>
        )}
        <div className='experiments-footer'>
          {experimentCount} experiment{experimentCount !== 1 ? 's' : ''}{' '}
          &middot; {counts.running} running &middot; {counts.created} created
          &middot; {counts.completed} completed
        </div>
      </>
    )
  }

  return (
    <div data-test='experiments-page' className='app-container container'>
      <PageTitle
        title='Experiments'
        cta={
          hasWarehouse ? (
            <Button onClick={() => setIsCreating(true)}>
              <IonIcon icon={addOutline} className='me-1' />
              Create Experiment
            </Button>
          ) : undefined
        }
      />
      {renderBody()}
    </div>
  )
}

export default ExperimentsPage
