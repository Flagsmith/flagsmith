import { useMemo } from 'react'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import type { Experiment, ExperimentStatus } from 'common/types/responses'

const FREEZE_STATUSES: ExperimentStatus[] = ['running', 'paused']

export function useFeatureExperimentFreeze(
  featureId: number | undefined,
  environmentId: string,
): {
  isFrozen: boolean
  experiment: Experiment | null
  isLoading: boolean
} {
  const { data, isLoading } = useGetExperimentsQuery(
    { environmentId, page_size: 100 },
    { skip: !featureId },
  )

  const experiment = useMemo(() => {
    if (!featureId || !data?.results) return null
    return (
      data.results.find(
        (e) =>
          e.feature?.id === featureId && FREEZE_STATUSES.includes(e.status),
      ) ?? null
    )
  }, [data?.results, featureId])

  return {
    experiment,
    isFrozen: experiment !== null,
    isLoading,
  }
}
