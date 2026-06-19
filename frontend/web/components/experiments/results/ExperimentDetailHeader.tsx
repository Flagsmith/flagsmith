import { FC, useCallback, useMemo, useState } from 'react'
import moment from 'moment'
import StatusBadge from 'components/experiments/StatusBadge'
import Button from 'components/base/forms/Button'
import ButtonDropdown from 'components/base/forms/ButtonDropdown'
import Icon from 'components/icons/Icon'
import { colorIconAction, colorIconSecondary } from 'common/theme/tokens'
import {
  useCompleteExperimentMutation,
  useDeleteExperimentMutation,
  usePauseExperimentMutation,
  useStartExperimentMutation,
  useUpdateExperimentMutation,
} from 'common/services/useExperiment'
import { Experiment } from 'common/types/responses'
import Tooltip from 'components/Tooltip'
import { getPrimaryMetric } from 'components/experiments/constants'
import 'components/base/SelectableCard/SelectableCard.scss'
import './results.scss'

type ExperimentDetailHeaderProps = {
  experiment: Experiment
  environmentId: string
}

const ExperimentDetailHeader: FC<ExperimentDetailHeaderProps> = ({
  environmentId,
  experiment,
}) => {
  const [startExperiment] = useStartExperimentMutation()
  const [pauseExperiment] = usePauseExperimentMutation()
  const [completeExperiment] = useCompleteExperimentMutation()
  const [deleteExperiment] = useDeleteExperimentMutation()
  const [updateExperiment, { isLoading: isUpdating }] =
    useUpdateExperimentMutation()

  const [isEditingHypothesis, setIsEditingHypothesis] = useState(false)
  const [hypothesisDraft, setHypothesisDraft] = useState('')

  const params = useMemo(
    () => ({ environmentId, experimentId: experiment.id }),
    [environmentId, experiment.id],
  )

  const handleStart = useCallback(async () => {
    try {
      await startExperiment(params).unwrap()
      toast('Experiment started')
    } catch {
      toast('Failed to start experiment', 'danger')
    }
  }, [startExperiment, params])

  const handlePause = useCallback(async () => {
    try {
      await pauseExperiment(params).unwrap()
      toast('Experiment paused')
    } catch {
      toast('Failed to pause experiment', 'danger')
    }
  }, [pauseExperiment, params])

  const handleComplete = useCallback(() => {
    openConfirm({
      body: (
        <span>
          Are you sure you want to end <strong>{experiment.name}</strong>? This
          action cannot be undone.
        </span>
      ),
      noText: 'Cancel',
      onYes: async () => {
        try {
          await completeExperiment(params).unwrap()
          toast('Experiment completed')
        } catch {
          toast('Failed to complete experiment', 'danger')
        }
      },
      title: 'End experiment?',
      yesText: 'End Experiment',
    })
  }, [completeExperiment, experiment.name, params])

  const handleDelete = useCallback(() => {
    openConfirm({
      body: (
        <span>
          Are you sure you want to delete <strong>{experiment.name}</strong>?
          This action cannot be undone.
        </span>
      ),
      destructive: true,
      noText: 'Cancel',
      onYes: async () => {
        try {
          await deleteExperiment(params).unwrap()
          toast('Experiment deleted')
        } catch {
          toast('Failed to delete experiment', 'danger')
        }
      },
      title: 'Delete experiment?',
      yesText: 'Delete',
    })
  }, [deleteExperiment, experiment.name, params])

  const startEditingHypothesis = () => {
    setHypothesisDraft(experiment.hypothesis ?? '')
    setIsEditingHypothesis(true)
  }

  const cancelHypothesis = () => {
    setIsEditingHypothesis(false)
  }

  const commitHypothesis = async () => {
    if (isUpdating) return
    const trimmed = hypothesisDraft.trim()
    if (trimmed === (experiment.hypothesis ?? '')) {
      setIsEditingHypothesis(false)
      return
    }
    try {
      await updateExperiment({
        body: { hypothesis: trimmed },
        ...params,
      }).unwrap()
      setIsEditingHypothesis(false)
    } catch {
      toast('Failed to update hypothesis', 'danger')
    }
  }

  const metric = getPrimaryMetric(experiment)
  const metricName = metric?.metric_name
  const startedFact = experiment.started_at
    ? `started ${moment(experiment.started_at).format('D MMM YYYY')}`
    : null
  const endedFact = experiment.ended_at
    ? `ended ${moment(experiment.ended_at).format('D MMM YYYY')}`
    : null

  const hasMetric = !!metric

  const renderActions = () => {
    switch (experiment.status) {
      case 'created':
        return (
          <Tooltip
            plainText
            place='bottom'
            title={
              <Button disabled={!hasMetric} onClick={handleStart} size='small'>
                Start Experiment
              </Button>
            }
          >
            {hasMetric
              ? null
              : 'A metric must be attached before starting the experiment'}
          </Tooltip>
        )
      case 'paused':
        return (
          <Button onClick={handleStart} size='small'>
            Resume Experiment
          </Button>
        )
      case 'running':
        return (
          <ButtonDropdown
            dropdownItems={[
              { label: 'Pause Experiment', onClick: handlePause },
            ]}
            onClick={handleComplete}
            size='small'
            theme='danger'
          >
            End Experiment
          </ButtonDropdown>
        )
      case 'completed':
        return (
          <Button onClick={handleDelete} size='small' theme='danger'>
            Delete Experiment
          </Button>
        )
      default:
        return null
    }
  }

  const renderHypothesis = () => {
    if (isEditingHypothesis) {
      return (
        <div className='mt-3' style={{ maxWidth: 640 }}>
          <span className='fs-caption text-muted fw-bold'>Hypothesis</span>
          <div className='d-flex align-items-start gap-2 mt-1'>
            <textarea
              autoFocus
              disabled={isUpdating}
              className='form-control'
              rows={3}
              value={hypothesisDraft}
              onChange={(e) => setHypothesisDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  commitHypothesis()
                }
                if (e.key === 'Escape') {
                  cancelHypothesis()
                }
              }}
            />
            <div className='d-flex flex-column gap-1'>
              <Button
                theme='text'
                onClick={commitHypothesis}
                onMouseDown={(e: React.MouseEvent) => e.preventDefault()}
                aria-label='Save hypothesis'
              >
                <Icon
                  name='checkmark-circle'
                  width={20}
                  fill={colorIconAction}
                />
              </Button>
              <Button
                theme='text'
                onClick={cancelHypothesis}
                onMouseDown={(e: React.MouseEvent) => e.preventDefault()}
                aria-label='Cancel'
              >
                <Icon
                  name='close-circle'
                  width={20}
                  fill={colorIconSecondary}
                />
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return (
      <div className='mt-3' style={{ maxWidth: 640 }}>
        <span className='fs-caption text-muted fw-bold'>Hypothesis</span>
        <div className='d-flex align-items-start gap-1'>
          <p className='text-muted mb-0'>
            {experiment.hypothesis || (
              <span className='fst-italic'>No hypothesis</span>
            )}
          </p>
          <Button
            theme='text'
            onClick={startEditingHypothesis}
            aria-label='Edit hypothesis'
          >
            <Icon name='edit' width={14} />
          </Button>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className='mb-4'>
        <div className='flex-row justify-content-between align-items-center'>
          <div className='flex-row align-items-center gap-2'>
            <h2 className='text-default fw-bold mb-0' style={{ fontSize: 20 }}>
              {experiment.name}
            </h2>
            <StatusBadge status={experiment.status} />
          </div>
          {renderActions()}
        </div>
        <div className='d-flex align-items-center gap-2 fs-caption mt-2'>
          {metricName && <strong>{metricName}</strong>}
          {[startedFact, endedFact].filter(Boolean).length > 0 && (
            <span className='text-muted'>
              {metricName ? '· ' : ''}
              {[startedFact, endedFact].filter(Boolean).join(' · ')}
            </span>
          )}
        </div>
        {renderHypothesis()}
      </div>
    </>
  )
}

export default ExperimentDetailHeader
