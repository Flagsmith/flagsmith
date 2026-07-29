import { FC, useCallback, useMemo } from 'react'
import { ExperimentStatus } from 'common/types/responses'
import {
  useCompleteExperimentMutation,
  useDeleteExperimentMutation,
  usePauseExperimentMutation,
  useStartExperimentMutation,
} from 'common/services/useExperiment'
import { ENABLE_EXPERIMENT_LIFECYCLE } from 'components/experiments/constants'
import DropdownMenu from 'components/base/DropdownMenu'

type ExperimentActionDropdownProps = {
  experimentId: number
  experimentName: string
  status: ExperimentStatus
  environmentId: string
}

const ExperimentActionDropdown: FC<ExperimentActionDropdownProps> = ({
  environmentId,
  experimentId,
  experimentName,
  status,
}) => {
  const [startExperiment] = useStartExperimentMutation()
  const [pauseExperiment] = usePauseExperimentMutation()
  const [completeExperiment] = useCompleteExperimentMutation()
  const [deleteExperiment] = useDeleteExperimentMutation()

  const params = useMemo(
    () => ({ environmentId, experimentId }),
    [environmentId, experimentId],
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
          Are you sure you want to mark <strong>{experimentName}</strong> as
          completed? This action cannot be undone.
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
      title: 'Complete experiment?',
      yesText: 'Complete',
    })
  }, [completeExperiment, experimentName, params])

  const handleDelete = useCallback(() => {
    openConfirm({
      body: (
        <span>
          Are you sure you want to delete <strong>{experimentName}</strong>?
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
  }, [deleteExperiment, experimentName, params])

  const items = useMemo(() => {
    switch (status) {
      case 'created':
        return [
          { label: 'Start Experiment', onClick: handleStart },
          {
            className: 'text-danger',
            label: 'Delete',
            onClick: handleDelete,
          },
        ]
      case 'running':
        return [
          ...(ENABLE_EXPERIMENT_LIFECYCLE
            ? [{ label: 'Pause Experiment', onClick: handlePause }]
            : []),
          { label: 'Mark as Completed', onClick: handleComplete },
        ]
      case 'paused':
        return [
          { label: 'Resume Experiment', onClick: handleStart },
          { label: 'Mark as Completed', onClick: handleComplete },
        ]
      case 'completed':
        return [
          {
            className: 'text-danger',
            label: 'Delete',
            onClick: handleDelete,
          },
        ]
      default:
        return []
    }
  }, [status, handleStart, handlePause, handleComplete, handleDelete])

  return <DropdownMenu items={items} />
}

export default ExperimentActionDropdown
