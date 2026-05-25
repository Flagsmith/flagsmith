import { FC, useState } from 'react'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import Button from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import CreateExperimentWizard from 'components/experiments/CreateExperimentWizard'
import { IonIcon } from '@ionic/react'
import { addOutline, flaskOutline } from 'ionicons/icons'

const ExperimentsPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const [isCreating, setIsCreating] = useState(false)

  const { data: experiments, isLoading } = useGetExperimentsQuery(
    { environmentId: environmentId ?? '' },
    { skip: !environmentId },
  )

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
          onCancel={() => setIsCreating(false)}
          onCreated={() => setIsCreating(false)}
        />
      </div>
    )
  }

  const experimentCount = experiments?.length ?? 0

  const renderBody = () => {
    if (isLoading) {
      return (
        <div className='text-center'>
          <Loader />
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
          <Button onClick={() => setIsCreating(true)}>
            <IonIcon icon={addOutline} className='me-1' />
            Create Experiment
          </Button>
        }
      />
      {renderBody()}
    </div>
  )
}

export default ExperimentsPage
