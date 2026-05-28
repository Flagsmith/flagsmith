import { FC, useState } from 'react'
import { useHistory } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import { useGetWarehouseConnectionsQuery } from 'common/services/useWarehouseConnection'
import Button from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import CreateExperimentWizard from 'components/experiments/CreateExperimentWizard'
import Icon from 'components/icons/Icon'

const ExperimentsPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const [isCreating, setIsCreating] = useState(false)
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
          <Icon
            name='setting'
            width={48}
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
          <Icon
            name='flask'
            width={48}
            className='text-muted mb-3 d-block mx-auto'
          />
          <h5>No experiments yet</h5>
          <p className='text-muted mb-4'>
            Create your first experiment to start testing hypotheses with your
            feature flags.
          </p>
          <Button onClick={() => setIsCreating(true)}>
            <Icon name='plus' width={16} />
            Create Experiment
          </Button>
        </div>
      )
    }
    return (
      <div className='mt-3'>
        <p className='text-muted'>
          {experimentCount} experiment{experimentCount !== 1 ? 's' : ''}
        </p>
      </div>
    )
  }

  return (
    <div data-test='experiments-page' className='app-container container'>
      <PageTitle
        title='Experiments'
        cta={
          hasWarehouse ? (
            <Button onClick={() => setIsCreating(true)}>
              <Icon name='plus' width={16} />
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
