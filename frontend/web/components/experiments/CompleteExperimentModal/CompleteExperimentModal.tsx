import { FC, useMemo, useState } from 'react'
import {
  useCompleteExperimentMutation,
  useGetExperimentBayesianResultsQuery,
  useGetExperimentQuery,
} from 'common/services/useExperiment'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import Banner from 'components/base/Banner'
import Button from 'components/base/forms/Button'
import ModalHR from 'components/modals/ModalHR'
import { getVariantIdentities } from 'components/experiments/results/derive'
import RolloutDecisionPicker from './RolloutDecisionPicker'
import {
  RolloutSelection,
  buildCompleteExperimentBody,
  getControlSelectedMessage,
  getDefaultSelection,
  getServedVariant,
  getVariantChoices,
} from './utils'

type CompleteExperimentModalProps = {
  environmentId: string
  experimentId: number
}

const CompleteExperimentModal: FC<CompleteExperimentModalProps> = ({
  environmentId,
  experimentId,
}) => {
  const params = { environmentId, experimentId }
  const { data: experiment, isError } = useGetExperimentQuery(params)
  const { data: bayesianResults, isLoading: isLoadingResults } =
    useGetExperimentBayesianResultsQuery(params)
  const { data: environment } = useGetEnvironmentQuery({ id: environmentId })
  const [completeExperiment, { isLoading: isCompleting }] =
    useCompleteExperimentMutation()
  const [selection, setSelection] = useState<RolloutSelection>()

  const results = bayesianResults?.payload ?? undefined
  const choices = useMemo(
    () => (experiment ? getVariantChoices(experiment, results) : []),
    [experiment, results],
  )
  const defaultSelection = useMemo(
    () =>
      experiment ? getDefaultSelection(experiment, choices, results) : null,
    [experiment, choices, results],
  )

  if (isError) {
    return (
      <div className='modal-body'>
        <div className='alert alert-danger mb-0'>
          We couldn't load this experiment.
        </div>
      </div>
    )
  }

  if (!experiment || !environment || !defaultSelection || isLoadingResults) {
    return (
      <div className='modal-body text-center'>
        <Loader />
      </div>
    )
  }

  const activeSelection = selection ?? defaultSelection
  const control = getVariantIdentities(experiment.feature)[0]
  const servedVariant = getServedVariant(activeSelection, control, choices)
  const hasAudience = !!experiment.experiment_rollout?.audience?.segments.length

  const handleComplete = async () => {
    try {
      await completeExperiment({
        ...params,
        body: buildCompleteExperimentBody(activeSelection),
      }).unwrap()
      toast('Experiment completed')
      closeModal()
    } catch {
      toast('Failed to complete experiment', 'danger')
    }
  }

  return (
    <>
      <div className='modal-body d-flex flex-column gap-3 mx-0'>
        <p className='mb-0'>
          Choose what <b>{experiment.feature.name}</b> serves in{' '}
          <b>{environment.name}</b> after <b>{experiment.name}</b> ends. Results
          stay available; this can't be undone.
        </p>
        {defaultSelection.decision === 'control' &&
          activeSelection.decision === 'control' && (
            <Banner>{getControlSelectedMessage(experiment, results)}</Banner>
          )}
        <RolloutDecisionPicker
          choices={choices}
          control={control}
          environmentName={environment.name}
          featureName={experiment.feature.name}
          selection={activeSelection}
          onChange={setSelection}
        />
        <div className='bg-surface-muted rounded-md p-3'>
          The experiment's rollout override is removed and{' '}
          {servedVariant ? (
            <>
              <b>100% of users</b> get <b>{servedVariant.name}</b>.
            </>
          ) : (
            <>
              <b>{experiment.feature.name}</b> is turned off for everyone.
            </>
          )}
          {hasAudience && (
            <>
              {' '}
              This applies to everyone in <b>{environment.name}</b>, not only
              the experiment's audience.
            </>
          )}
        </div>
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button className='mr-2' onClick={closeModal} theme='secondary'>
          Cancel
        </Button>
        <Button
          disabled={
            isCompleting ||
            (!servedVariant && activeSelection.decision !== 'disable')
          }
          onClick={handleComplete}
        >
          Complete experiment
        </Button>
      </div>
    </>
  )
}

export default CompleteExperimentModal
